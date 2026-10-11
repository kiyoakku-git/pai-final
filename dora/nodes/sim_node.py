"""sim node: owns the Genesis world.

inputs : look    (json {"req", "label"})              -> renders the eye camera and sends `image`
         command (json {"req", "action", ...})        -> moves the arm, then sends `done`
outputs: image   (float32 HxWx6 = RGB + world XYZ per pixel, metadata: req, label, truth)
         done    (json {"req", "truth"})
"""
import json
import os

import numpy as np
from dora import Node

from common import ROOT, read_json, send_array, send_json
import genesis as gs
from scene import build_scene, BLOCK_SIZE
from robot import Arm
from util import to_np


def truth(blocks):
    """Ground-truth block positions, used only for logging/evaluation (never for control)."""
    return {name: to_np(b.get_pos()).round(4).tolist() for name, b in blocks.items()}


def main():
    backend = gs.cpu if os.environ.get("BACKEND") == "cpu" else gs.gpu
    scene, franka, blocks, eye_cam, video_cam = build_scene(backend=backend)
    arm = Arm(scene, franka)
    arm.step(50)
    video = os.path.join(ROOT, os.environ.get("VIDEO", "outputs/dora/video.mp4"))
    os.makedirs(os.path.dirname(video), exist_ok=True)
    video_cam.start_recording(save_to_filename=video, fps=25)

    node = Node()
    for event in node:
        if event["type"] != "INPUT":
            if event["type"] == "STOP":
                break
            continue
        msg = read_json(event)
        if event["id"] == "look":
            rgb, *_ = eye_cam.render(rgb=True)
            pc, mask = eye_cam.render_pointcloud()
            xyz = np.where(to_np(mask)[..., None].astype(bool), to_np(pc), np.nan)
            frame = np.concatenate([to_np(rgb), xyz], axis=-1).astype(np.float32)
            send_array(node, "image", frame,
                       {"req": msg["req"], "label": msg["label"], "truth": json.dumps(truth(blocks))})
        elif event["id"] == "command":
            if msg["action"] == "pick_place":
                arm.pick(msg["pick"])
                arm.place(msg["place"])
                arm.go_home()
                send_json(node, "done", {"req": msg["req"], "truth": truth(blocks)})
            elif msg["action"] == "finish":
                arm.step(50)
                break

    video_cam.stop_recording()
    print(f"[sim] saved {video}", flush=True)


if __name__ == "__main__":
    main()
