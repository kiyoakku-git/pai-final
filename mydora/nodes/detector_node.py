# detector_node.py R6-2 planner から届いた名前で探す


import numpy as np
from PIL import Image
from dora import Node
from transformers import pipeline
import json
import pyarrow as pa

OWLv2 = pipeline("zero-shot-object-detection", model="google/owlv2-base-patch16-ensemble")    # 言葉で指定した物を、画像から探す
threshold=0.1

node = Node()

for event in node:
    if event["type"] == "INPUT":

        md = event["metadata"]
        pict = event["value"].to_numpy().reshape(json.loads(md["shape"]))
        # print(pict.shape)
        labels = json.loads(md["labels"]) # planner から届いた名前のリスト red block, yellow block など

        image_rgb = Image.fromarray(pict[:, :, 0:3].astype(np.uint8))
        xyz = (pict[:, :, 3:6])   # xyz座標

        positions = {}
        for label in labels:

            candidate_labels=[label]
            result = OWLv2(image_rgb, candidate_labels=candidate_labels, threshold=threshold)  # 物体検出
            # print(result[0])

            xmin, ymin, xmax, ymax = (result[0]["box"]["xmin"], result[0]["box"]["ymin"], result[0]["box"]["xmax"], result[0]["box"]["ymax"])
            cx = int((xmin + xmax)/2)   # box の中心の x（列）
            cy = int((ymin + ymax)/2)   # box の中心の y（行）

            pos = xyz[cy, cx]  # box の中心の点の座標

            positions[label] = pos.tolist()

        image_rgb.save("look.png")
        node.send_output("detection", pa.array([json.dumps(positions)])) # pos の座標をnumpy からlistに変換して送信

    if event["type"] == "STOP":
        break

