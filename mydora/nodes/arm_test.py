# arm_test.py   R2-3a

import numpy as np
import genesis as gs
from PIL import Image


gs.init()
stage = gs.Scene(show_viewer=False)
stage.add_entity(gs.morphs.Plane())
surface=gs.surfaces.Default(color=(0.85, 0.10, 0.10))
stage.add_entity(gs.morphs.Box(pos=(0.5, 0.5, 0.02), size=(0.04, 0.04, 0.04)), surface=surface)
cam = stage.add_camera(res=(640, 480), fov=60, pos=(1.5, 1.5, 1.0), lookat=(0.0, 0.0, 0.5))
franka = stage.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))

stage.build()

# set_dofs_kp / set_dofs_kv / set_dofs_position
HOME_QPOS = np.array([0.0, -0.3, 0.0, -2.2, 0.0, 2.0, 0.79, 0.04, 0.04])
KP = np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100])
# KP = np.array([450, 450, 350, 350, 200, 200, 200, 10, 10])
KV = np.array([450, 450, 350, 350, 200, 200, 200, 10, 10])

franka.set_dofs_kp(KP)
franka.set_dofs_kv(KV)
franka.set_dofs_position(HOME_QPOS)
franka.control_dofs_position(HOME_QPOS)

for _ in range(100):
    stage.step()  # 1 step = 0.01s, so 100 steps = 1s       

target = np.array([0.5, 0.5, 0.17])         # Zをブロックの中心にするため2cm足した

ARM_DOFS = np.arange(7)                     # 関節の番号配列 0-6 の７個
FINGER_DOFS = np.arange(7, 9)               # 指の位置 7-8 の２個
DOWN_QUAT = np.array([0.0, 1.0, 0.0, 0.0])  # グリッパーが真下に向ける向き
HAND_TO_GRASP = 0.11                        # handから指先までの距離

def to_np(x):  # Genesisの出力をGPUからCPUに移動し、float numpy arrayに変換する
    x = x.detach().cpu().numpy()
    return np.asarray(x, dtype=float)   

def arm_q():   # 現在のアームの関節角度を取得する
    return to_np(franka.get_dofs_position(ARM_DOFS))

def move_to(grasp_pos, steps=100):   # アームポジションを指定位置に移動して、グリッパーを下げる
    target = np.asarray(grasp_pos, dtype=float) + np.array([0.0, 0.0, HAND_TO_GRASP])
    
    quat = DOWN_QUAT
    q_goal = to_np(franka.inverse_kinematics(link=hand, pos=target, quat=quat))[: len(ARM_DOFS)]
    q_start = arm_q()

    for i in range(1, steps + 1):
        a = i / steps
        a = a * a * (3 - 2 * a)  # smoothstep: slow start and stop
        franka.control_dofs_position(q_start + a * (q_goal - q_start), ARM_DOFS)
        stage.step()
    for _ in range(20):
        stage.step()  # 1 step = 0.01s, so 100 steps = 1s       


hand = franka.get_link("hand")
move_to(target)

print( "hand pos:", hand.get_pos())
print( "target:", target+ np.array([0.0, 0.0, HAND_TO_GRASP]) )  # handの位置はtargetよりHAND_TO_GRASPだけ上にある



pict = cam.render(rgb=True)[0]
Image.fromarray(pict).save("look.png")

print(pict.shape)
