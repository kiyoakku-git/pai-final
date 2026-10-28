# sim_node.py

import genesis as gs
from PIL import Image


gs.init()
stage = gs.Scene(show_viewer=False)
stage.add_entity(gs.morphs.Plane())
stage.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))
surface=gs.surfaces.Default(color=(0.85, 0.10, 0.10))
stage.add_entity(gs.morphs.Box(pos=(0.5, 0.5, 0.02), size=(0.04, 0.04, 0.04)), surface=surface)

cam = stage.add_camera(res=(640, 480), fov=60, pos=(1.5, 1.5, 1.0), lookat=(0.0, 0.0, 0.5))
stage.build()
stage.step()

pict = cam.render(rgb=True)[0]
Image.fromarray(pict).save("look.png")

print(pict.shape)
