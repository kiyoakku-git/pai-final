# planner_node.py   R2-3d, R4

import json
import os
from dora import Node
import pyarrow as pa


msg = {"pick": [0.5, 0.5, 0.02], "place": [0.4, -0.3, 0.02]}

send_message = False
node = Node()

for event in node:
    if event["type"] == "STOP":
        break
    if event["id"] == "tick":
        if not send_message:
            send_message = True
            node.send_output("command", pa.array([json.dumps(msg)]))
        
    if event["id"] == "done":
        json_msg = json.loads(event["value"].to_pylist()[0])
        print( "ブロックの位置:", json_msg["block_pos"])
        print( "ブロックを置くべき位置:", msg["place"] )

