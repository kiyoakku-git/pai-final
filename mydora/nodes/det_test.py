# det_test.py R3.1

import numpy as np
import genesis as gs
from PIL import Image

from transformers import pipeline

gs.init()
stage = gs.Scene(show_viewer=False)
stage.add_entity(gs.morphs.Plane())
surface=gs.surfaces.Default(color=(0.85, 0.10, 0.10))
box =stage.add_entity(gs.morphs.Box(pos=(0.5, 0.5, 0.02), size=(0.04, 0.04, 0.04)), surface=surface)
cam = stage.add_camera(res=(640, 480), fov=60, pos=(0.8, 0.8, 0.5), lookat=(0.5, 0.5, 0.0))
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

pict = cam.render(rgb=True)[0]
img = Image.fromarray(pict)
img.save("look.png")


OWLv2 = pipeline("zero-shot-object-detection", model="google/owlv2-base-patch16-ensemble")    # 言葉で指定した物を、画像から探す
candidate_labels=["red block"]
threshold=0.1

result  = OWLv2(img, candidate_labels=candidate_labels, threshold=threshold)  # 物体検出
print(result[0])

xmin, ymin, xmax, ymax = (result[0]["box"]["xmin"], result[0]["box"]["ymin"], result[0]["box"]["xmax"], result[0]["box"]["ymax"])
cx = int((xmin + xmax)/2)   # box の中心の x（列）
cy = int((ymin + ymax)/2)   # box の中心の y（行）

pointcloud = cam.render_pointcloud()
PC, mask = pointcloud
pos = PC[cy, cx]  # box の中心の点の座標

print ("type of pointcloud:", type(pointcloud))

print ("pointcloud   :", pos)
print ("box.get_pos():", box.get_pos())

