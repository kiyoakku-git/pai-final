"""Check that OWLv2 can find each block in the robot's camera image and locate it in 3D."""
import os
import sys

import numpy as np
import genesis as gs
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scene import build_scene  # noqa: E402
from perception import Detector, box_to_world, draw_detections  # noqa: E402

backend = gs.cpu if "--cpu" in sys.argv else gs.gpu
scene, franka, blocks, eye_cam, video_cam = build_scene(backend=backend)
scene.step()
rgb, *_ = eye_cam.render(rgb=True)
pc, mask = eye_cam.render_pointcloud()
os.makedirs("outputs", exist_ok=True)
Image.fromarray(np.asarray(rgb)).save("outputs/eye_cam.png")

detector = Detector()
labels = list(blocks.keys())
all_dets = []
for name in labels:
    dets = detector.detect(rgb, [name])
    if not dets:
        print(f"{name:12s} NOT FOUND")
        continue
    best = dets[0]
    all_dets.append(best)
    est = box_to_world(best["box"], pc, mask)
    true = np.asarray(blocks[name].get_pos()).astype(float)
    err = np.linalg.norm(est[:2] - true[:2]) * 1000 if est is not None else float("nan")
    print(f"{name:12s} score={best['score']:.2f} est={np.round(est, 3)} true={np.round(true, 3)} xy_error={err:.1f} mm")
draw_detections(rgb, all_dets, "outputs/detect_check.png")
print("saved outputs/eye_cam.png and outputs/detect_check.png")
