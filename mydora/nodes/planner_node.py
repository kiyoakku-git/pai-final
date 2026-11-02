# planner_node.py   R6−2, R6-3

import json
from dora import Node
import pyarrow as pa
import numpy as np


plan = {"pick": "red block", "place_on": "yellow block"}

send_message = False
node = Node()

for event in node:
    if event["type"] == "STOP":
        break
    if event["type"] == "INPUT":

        if event["id"] == "tick": # 最初のtickの合図のみ受ける
            if not send_message:
                send_message = True
                node.send_output("look",pa.array([json.dumps([plan["pick"], plan["place_on"]])]))

        if event["id"] == "detection": 
            msg = json.loads(event["value"].to_pylist()[0])

            pick_pos = np.array(msg[plan["pick"]]) + np.array([0.0, 0.0, -0.02])  # 0.02m下げる: 下のblock
            place_pos = np.array(msg[plan["place_on"]]) + np.array([0.0, 0.0, 0.02])  # 0.02m上げる：上のblock
            new_msg = {"pick": pick_pos.tolist(), "place": place_pos.tolist()} # blockの移動先の設定
            node.send_output("command", pa.array([json.dumps(new_msg)]))
   
        if event["id"] == "done":
            json_msg = json.loads(event["value"].to_pylist()[0])
            print( "ブロックの位置:", json_msg["block_pos"])
            print( "ブロックを置くべき位置:", new_msg["place"])
