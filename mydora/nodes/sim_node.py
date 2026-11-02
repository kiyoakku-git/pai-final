# sim_node.py  R6-2（sim に黄色を足す）,R6-3

import genesis as gs
import numpy as np
from dora import Node
import json
import pyarrow as pa


gs.init() # 床、アーム、BOXを表示するために必要な初期化処理
stage = gs.Scene(show_viewer=False)
stage.add_entity(gs.morphs.Plane())

# blockの定義
red_surface    = gs.surfaces.Default(color=(0.85, 0.10, 0.10))
yellow_surface = gs.surfaces.Default(color=(0.90, 0.80, 0.10))

boxes = {}  # 空の辞書
boxes["red block"]    = stage.add_entity(gs.morphs.Box(pos=(0.5, 0.5, 0.02), size=(0.04, 0.04, 0.04)), surface=red_surface)
boxes["yellow block"] = stage.add_entity(gs.morphs.Box(pos=(0.5, 0.35, 0.02), size=(0.04, 0.04, 0.04)), surface=yellow_surface)



cam = stage.add_camera(res=(640, 480), fov=60, pos=(0.8, 0.8, 0.5), lookat=(0.5, 0.5, 0.0))
video_cam = stage.add_camera(res=(640, 480), fov=60, pos=(1.6, 0.1, 0.9), lookat=(0.4, 0.1, 0.1)) # 録画用カメラ

franka = stage.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))

stage.build() # 設定したものを反映させるためにbuild()する


# set_dofs_kp / set_dofs_kv / set_dofs_position
HOME_QPOS = np.array([0.0, -0.3, 0.0, -2.2, 0.0, 2.0, 0.79, 0.04, 0.04])
KP = np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100])
# KP = np.array([450, 450, 350, 350, 200, 200, 200, 10, 10])
KV = np.array([450, 450, 350, 350, 200, 200, 200, 10, 10])

franka.set_dofs_kp(KP)
franka.set_dofs_kv(KV)
franka.set_dofs_position(HOME_QPOS)
franka.control_dofs_position(HOME_QPOS)

for _ in range(100): # build()後に、control_dofs_position した後に１秒待つ
    stage.step()

ARM_DOFS = np.arange(7)                     # 関節の番号配列 0-6 の７個
FINGER_DOFS = np.arange(7, 9)               # 指の位置 7-8 の２個
DOWN_QUAT = np.array([0.0, 1.0, 0.0, 0.0])  # グリッパーが真下に向ける向き
HAND_TO_GRASP = 0.11                        # handから指先までの距離
APPROACH = 0.15                             # grasp pointの上にあるアプローチ位置までの距離


def to_np(x):  # Genesisの出力をGPUからCPUに移動し、float numpy arrayに変換する
    x = x.detach().cpu().numpy()
    return np.asarray(x, dtype=float)   

def arm_q():   # 現在のアームの関節角度を取得する
    return to_np(franka.get_dofs_position(ARM_DOFS))

def open_gripper():  # グリッパーを開く
    franka.control_dofs_position(np.array([0.04, 0.04]), FINGER_DOFS)   
    for _ in range(40):
        step_rec()

def close_gripper(steps=40):  # グリッパーを閉じる
    franka.control_dofs_position(np.array([0.0, 0.0]), FINGER_DOFS)   
    for _ in range(steps):
        step_rec()

def move_to(grasp_pos, steps=100):   # アームポジションを指定位置に移動して、グリッパーを下げる
    target = np.asarray(grasp_pos, dtype=float) + np.array([0.0, 0.0, HAND_TO_GRASP])
    
    quat = DOWN_QUAT
    q_goal = to_np(franka.inverse_kinematics(link=hand, pos=target, quat=quat))[: len(ARM_DOFS)]
    q_start = arm_q()

    for i in range(1, steps + 1):
        a = i / steps
        a = a * a * (3 - 2 * a)  # スムーズなステップ: スルースタート、スローストップ
        franka.control_dofs_position(q_start + a * (q_goal - q_start), ARM_DOFS)
        step_rec()
    for _ in range(20):
        step_rec()

def step_rec(n=1): # 録画用カメラの映像を録画しながら、nステップ進める
    for _ in range(n):
        stage.step()
        
hand = franka.get_link("hand")


node = Node()

for event in node:
    if event["type"] == "INPUT":
        if event["id"] == "look":

            pict = cam.render(rgb=True)[0]
            pointcloud = cam.render_pointcloud()
            PC, mask = pointcloud

            img = np.concatenate([pict, PC], axis=2).astype(np.float32)
            labels = json.loads(event["value"].to_pylist()[0])
            metadata = {"shape": json.dumps(list(img.shape)), "labels": json.dumps(labels)}
                        
            node.send_output("image", pa.array(img.ravel()), metadata=metadata)

        if event["id"] == "command":
            json_msg = json.loads(event["value"].to_pylist()[0])
            pos0 = np.array(json_msg["pick"])
            pos1 = pos0 + np.array([0.0, 0.0, 0.15])    # blockの真上
            pos2 = pos0 + np.array([0.0, 0.0, 0.20])    # blockを持ち上げた位置
            pos3 = np.array(json_msg["place"]) + np.array([0.0, 0.0, 0.20])    # blockを運んで置く位置
            pos4 = np.array(json_msg["place"]) + np.array([0.0, 0.0, 0.010])    # blockを離す位置 

            stage.step()

            video_cam.start_recording(save_to_filename="r6_demo.mp4", fps=50) # 録画開始
            open_gripper()   # グリッパーを開く
            move_to(pos1)    # blockの真上
            move_to(pos0)    # blockの初期位置
            close_gripper()  # グリッパーを閉じる
            move_to(pos2)    # blockを持ち上げる
            move_to(pos3)    # blockを運ぶ
            move_to(pos4)    # blockを離す位置まで下ろす
            open_gripper()   #グリッパーを開く

            video_cam.stop_recording() # 録画終了、保存

            box_pos = {}
            for name, box in boxes.items():
                box_pos[name] = box.get_pos().tolist()
            out_msg = {"block_pos": box_pos}
            node.send_output("done", pa.array([json.dumps(out_msg)]))         


    if event["type"] == "STOP": 
        break


    