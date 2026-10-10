"""Pick the red and blue blocks using their true positions and put them in the tray (no AI yet)."""
import os
import sys

import numpy as np
import genesis as gs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scene import build_scene, TRAY_CENTER, BLOCK_SIZE  # noqa: E402
from robot import Arm  # noqa: E402

backend = gs.cpu if "--cpu" in sys.argv else gs.gpu
scene, franka, blocks, eye_cam, video_cam = build_scene(backend=backend)
arm = Arm(scene, franka)
arm.step(50)

os.makedirs("outputs", exist_ok=True)
video_cam.start_recording(save_to_filename="outputs/pick_check.mp4", fps=25)
for name in ["red block", "blue block"]:
    start = np.asarray(blocks[name].get_pos()).astype(float)
    arm.pick(start)
    arm.place([TRAY_CENTER[0], TRAY_CENTER[1], BLOCK_SIZE / 2])
    arm.step(50)
    end = np.asarray(blocks[name].get_pos()).astype(float)
    inside = abs(end[0] - TRAY_CENTER[0]) < 0.08 and abs(end[1] - TRAY_CENTER[1]) < 0.08
    print(f"{name:12s} start={np.round(start, 3)} end={np.round(end, 3)} in_tray={inside}")
video_cam.stop_recording()
print("saved outputs/pick_check.mp4")
