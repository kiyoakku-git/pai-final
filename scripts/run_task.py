"""Main demo: a language instruction -> OWLv2 detection -> IK pick-and-place -> camera check (retry on failure).

Usage (Mac):
    python scripts/run_task.py "put the red block in the tray"
    python scripts/run_task.py "clean up all the blocks"
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import genesis as gs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scene import build_scene, BLOCK_SIZE, TRAY_CENTER, TRAY_SLOTS, in_tray  # noqa: E402
from robot import Arm  # noqa: E402
from perception import Detector, box_to_world, draw_detections  # noqa: E402
from instruction import parse_instruction  # noqa: E402
from util import to_np  # noqa: E402


def look(eye_cam, detector, label):
    """Find `label` in the eye camera image and return (world_pos or None, detection or None, rgb)."""
    rgb, *_ = eye_cam.render(rgb=True)
    pc, mask = eye_cam.render_pointcloud()
    dets = detector.detect(rgb, [label])
    if not dets:
        return None, None, rgb
    return box_to_world(dets[0]["box"], pc, mask, BLOCK_SIZE), dets[0], rgb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("instruction", nargs="?", default="put the red block in the tray")
    ap.add_argument("--max-tries", type=int, default=2)
    ap.add_argument("--out", default="outputs/run")
    ap.add_argument("--cpu", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    targets = parse_instruction(args.instruction)
    print(f'instruction: "{args.instruction}" -> targets: {targets}')
    if not targets:
        print("No known object in the instruction. Try e.g. 'put the red block in the tray'.")
        return

    detector = Detector()
    scene, franka, blocks, eye_cam, video_cam = build_scene(backend=gs.cpu if args.cpu else gs.gpu)
    arm = Arm(scene, franka)
    arm.step(50)
    video_cam.start_recording(save_to_filename=os.path.join(args.out, "video.mp4"), fps=25)

    log = {"instruction": args.instruction, "targets": targets, "results": []}
    slot = 0
    for name in targets:
        result = {"target": name, "tries": []}
        for attempt in range(1, args.max_tries + 1):
            pos, det, rgb = look(eye_cam, detector, name)
            draw_detections(rgb, [det] if det else [], os.path.join(args.out, f"{name.replace(' ', '_')}_try{attempt}.png"))
            if pos is None:
                print(f"[{name}] try {attempt}: not found")
                result["tries"].append({"found": False})
                break
            if in_tray(pos):
                print(f"[{name}] already in the tray")
                result["tries"].append({"found": True, "already_in_tray": True})
                break
            print(f"[{name}] try {attempt}: score={det['score']:.2f} pick at {np.round(pos, 3)}")
            dx, dy = TRAY_SLOTS[slot % len(TRAY_SLOTS)]
            arm.pick(pos)
            arm.place([TRAY_CENTER[0] + dx, TRAY_CENTER[1] + dy, BLOCK_SIZE / 2])
            arm.go_home()
            # Closed loop: look again with the camera to check the block really is in the tray.
            check, _, _ = look(eye_cam, detector, name)
            ok = check is not None and in_tray(check)
            truth_ok = in_tray(to_np(blocks[name].get_pos()))
            print(f"[{name}] try {attempt}: camera check={'OK' if ok else 'FAILED'} (ground truth {'OK' if truth_ok else 'NG'})")
            result["tries"].append({"found": True, "score": det["score"], "pick": pos.round(4).tolist(),
                                    "camera_ok": bool(ok), "truth_ok": bool(truth_ok)})
            if ok:
                slot += 1
                break
        result["success"] = bool(in_tray(to_np(blocks[name].get_pos())))
        log["results"].append(result)

    arm.step(50)
    video_cam.stop_recording()
    n_ok = sum(r["success"] for r in log["results"])
    log["summary"] = f"{n_ok}/{len(targets)} objects in the tray"
    with open(os.path.join(args.out, "log.json"), "w") as f:
        json.dump(log, f, indent=2)
    print(log["summary"])
    print(f"saved {args.out}/video.mp4, {args.out}/log.json and detection images")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"elapsed {time.time() - t0:.0f} s")
