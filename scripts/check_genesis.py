import time
import genesis as gs

gs.init(backend=gs.gpu)
scene = gs.Scene(show_viewer=False)
scene.add_entity(gs.morphs.Plane())
scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))
scene.build()
t = time.time()
for _ in range(200):
    scene.step()
print("steps/sec:", 200 / (time.time() - t))
