# viewer_node.py
import json
from dora import Node
from PIL import Image

node = Node()

for event in node:
    if event["type"] == "INPUT":

        md = event["metadata"]
        pict = event["value"].to_numpy().reshape(json.loads(md["shape"]))
        Image.fromarray(pict).save("look.png")
        print(pict.shape)

    if event["type"] == "stop":
        break

    