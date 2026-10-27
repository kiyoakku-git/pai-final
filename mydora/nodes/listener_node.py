# listener_node.py

from dora import Node
import json

node = Node()
for event in node:
    if event["type"] == "INPUT":
        text = event["value"].to_pylist()[0]
        data = json.loads(text)
        print(data["label"])
        print(data["count"])

        print(text, type(text))
        print(data, type(data))
