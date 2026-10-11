"""detector node: open-vocabulary detection (OWLv2) + 2D box -> 3D position.

input : image     (from sim; metadata label = what to look for)
output: detection (json {"req", "label", "found", "pos", "score", "box"})
"""
import json
import os

import numpy as np
from dora import Node

from common import read_array, send_json
from perception import box_to_world

THRESHOLD = float(os.environ.get("THRESHOLD", "0.1"))


class OracleDetector:
    """Test stand-in (DETECTOR=oracle): draws a box around the true position. Not used for the demo."""

    def detect(self, rgb, labels, xyz, truth):
        t = np.asarray(truth[labels[0]])
        d = np.linalg.norm(np.nan_to_num(xyz, nan=9.0) - t, axis=-1)
        if d.min() > 0.04:
            return []
        y, x = np.unravel_index(d.argmin(), d.shape)
        return [{"label": labels[0], "score": 1.0, "box": (x - 14, y - 14, x + 14, y + 14)}]


def main():
    if os.environ.get("DETECTOR") == "oracle":
        detector = OracleDetector()
    else:
        from perception import Detector

        owl = Detector()
        detector = type("Owl", (), {"detect": lambda self, rgb, labels, xyz, truth: owl.detect(rgb, labels, THRESHOLD)})()

    node = Node()
    for event in node:
        if event["type"] == "INPUT" and event["id"] == "image":
            md = event["metadata"]
            frame = read_array(event)
            rgb = frame[..., :3].astype(np.uint8)
            xyz = frame[..., 3:]
            dets = detector.detect(rgb, [md["label"]], xyz, json.loads(md["truth"]))
            out = {"req": md["req"], "label": md["label"], "found": False}
            if dets:
                best = dets[0]
                pos = box_to_world(best["box"], np.nan_to_num(xyz), ~np.isnan(xyz[..., 0]))
                if pos is not None:
                    out.update(found=True, pos=pos.round(4).tolist(), score=round(best["score"], 3),
                               box=[float(v) for v in best["box"]])
            print(f"[detector] {out}", flush=True)
            send_json(node, "detection", out)
        elif event["type"] in ("STOP", "INPUT_CLOSED"):
            break


if __name__ == "__main__":
    main()
