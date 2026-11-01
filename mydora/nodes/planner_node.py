# planner_node.py   R3-3

import json
from dora import Node
import pyarrow as pa
import numpy as np

no_msg = []
send_message = False
node = Node()

for event in node:
    if event["type"] == "STOP":
        break
    if event["type"] == "INPUT":

        if event["id"] == "tick": # 最初のtickの合図のみ受ける
            if not send_message:
                send_message = True
                node.send_output("look",pa.array([json.dumps(no_msg)]))

        if event["id"] == "detection": 
            msg = json.loads(event["value"].to_pylist()[0])
            msg = np.array(msg) + np.array([0.0, 0.0, -0.02])  # 0.02m下げる
            new_msg = {"pick": msg.tolist(), "place": [0.4, -0.3, 0.02]} # blockの移動先の設定
            node.send_output("command", pa.array([json.dumps(new_msg)]))
   
        if event["id"] == "done":
            json_msg = json.loads(event["value"].to_pylist()[0])
            print( "ブロックの位置:", json_msg["block_pos"])
            print( "ブロックを置くべき位置:", new_msg["place"])
