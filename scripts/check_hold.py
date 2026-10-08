import os
import numpy as np
import genesis as gs

gs.init(backend=gs.gpu)
scene = gs.Scene(show_viewer=False)
scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))
scene.add_entity(gs.morphs.Box(pos=(0.6, 0.0, 0.6), size=(0.05, 0.05, 0.05)))
cam = scene.add_camera(res=(640, 480), pos=(3.0, -1.5, 1.5), lookat=(0.3, 0.0, 0.3), fov=35, GUI=False)
scene.build()

home = np.array([0.0, -0.3, 0.0, -2.2, 0.0, 2.0, 0.79, 0.04, 0.04])
franka.set_dofs_kp(np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100]))
franka.set_dofs_kv(np.array([450, 450, 350, 350, 200, 200, 200, 10, 10]))
franka.set_dofs_position(home)

os.makedirs("outputs", exist_ok=True)
cam.start_recording(save_to_filename="outputs/check_hold.mp4", fps=50)
for _ in range(180):
    franka.control_dofs_position(home)
    scene.step()
cam.stop_recording()
print("saved outputs/check_hold.mp4")
