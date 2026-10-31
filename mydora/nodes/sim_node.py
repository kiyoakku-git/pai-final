# sim_node.py

import genesis as gs
import numpy as np
from dora import Node
import json
import pyarrow as pa


gs.init() # 床、アーム、BOXを表示するために必要な初期化処理
stage = gs.Scene(show_viewer=False)
stage.add_entity(gs.morphs.Plane())
stage.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))
surface=gs.surfaces.Default(color=(0.85, 0.10, 0.10))
stage.add_entity(gs.morphs.Box(pos=(0.5, 0.5, 0.02), size=(0.04, 0.04, 0.04)), surface=surface)
cam = stage.add_camera(res=(640, 480), fov=60, pos=(1.5, 1.5, 1.0), lookat=(0.0, 0.0, 0.5))
stage.build() # 設定したものを反映させるためにbuild()を呼ぶ必要がある

node = Node()

for event in node:
    if event["type"] == "INPUT":
        stage.step()
        pict = cam.render(rgb=True)[0]
        md = dict(shape=json.dumps(list(pict.shape)))
        node.send_output("image", pa.array(pict.ravel()), md)
        print("sim_node.py: sent image of shape", pict.shape)

    if event["type"] == "stop": 
        break
    