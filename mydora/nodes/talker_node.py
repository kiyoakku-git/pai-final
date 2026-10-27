# talker_node.py

import pyarrow as pa
from dora import Node
import json

node = Node()
Num = 0
for event in node:
    if event["type"] == "INPUT" :
        Num += 1
        msg = {"label": "red block", "count": Num}
        node.send_output("plusone", pa.array([json.dumps(msg)]))
        
    elif event["type"] == "STOP" or event["type"] == "INPUT_CLOSED":
        break
