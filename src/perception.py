"""Open-vocabulary detection (OWLv2) and pixel-to-3D lifting with the depth camera."""
import numpy as np
from PIL import Image, ImageDraw

from util import to_np

MODEL_ID = "google/owlv2-base-patch16-ensemble"


class Detector:
    def __init__(self, model_id=MODEL_ID):
        from transformers import pipeline

        self.pipe = pipeline("zero-shot-object-detection", model=model_id)

    def detect(self, rgb, labels, threshold=0.1):
        """Return detections sorted by score: [{'label', 'score', 'box': (xmin, ymin, xmax, ymax)}]."""
        img = Image.fromarray(np.asarray(to_np(rgb), dtype=np.uint8)).convert("RGB")
        out = self.pipe(img, candidate_labels=list(labels), threshold=threshold)
        dets = [
            {"label": d["label"], "score": float(d["score"]),
             "box": (d["box"]["xmin"], d["box"]["ymin"], d["box"]["xmax"], d["box"]["ymax"])}
            for d in out
        ]
        return sorted(dets, key=lambda d: -d["score"])


def box_to_world(box, pointcloud, mask, block_size=0.04):
    """Estimate the 3D center of a block from its detection box.

    The camera sees the top face of the block best, so we keep the highest points in the box (the top face),
    take their median x/y, and put z half a block below the top.
    """
    xmin, ymin, xmax, ymax = (int(round(v)) for v in box)
    pointcloud = to_np(pointcloud)
    mask = to_np(mask).astype(bool)
    pts = pointcloud[ymin:ymax + 1, xmin:xmax + 1].reshape(-1, 3)
    valid = mask[ymin:ymax + 1, xmin:xmax + 1].reshape(-1)
    pts = pts[valid]
    if len(pts) == 0:
        return None
    top_z = np.percentile(pts[:, 2], 95)
    top = pts[pts[:, 2] > top_z - 0.005]
    x, y = np.median(top[:, 0]), np.median(top[:, 1])
    return np.array([x, y, max(top_z - block_size / 2, block_size / 2)])


def draw_detections(rgb, dets, path):
    img = Image.fromarray(np.asarray(to_np(rgb), dtype=np.uint8)).convert("RGB")
    draw = ImageDraw.Draw(img)
    for d in dets:
        draw.rectangle(d["box"], outline=(255, 255, 0), width=3)
        draw.text((d["box"][0], max(0, d["box"][1] - 12)), f'{d["label"]} {d["score"]:.2f}', fill=(255, 255, 0))
    img.save(path)
