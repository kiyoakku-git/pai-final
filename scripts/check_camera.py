import os
import genesis as gs

gs.init(backend=gs.gpu)
scene = gs.Scene(show_viewer=False)
scene.add_entity(gs.morphs.Plane())
scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))
scene.add_entity(gs.morphs.Box(pos=(0.6, 0.0, 0.6), size=(0.05, 0.05, 0.05)))
cam = scene.add_camera(res=(640, 480), pos=(3.0, -1.5, 1.5), lookat=(0.3, 0.0, 0.3), fov=35, GUI=False)
scene.build()
os.makedirs("outputs", exist_ok=True)
cam.start_recording(save_to_filename="outputs/check_camera.mp4", fps=50)
for _ in range(180):
    scene.step()
cam.stop_recording()
print("saved outputs/check_camera.mp4")
