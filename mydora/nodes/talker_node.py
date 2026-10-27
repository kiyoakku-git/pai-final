# talker_node.py

import pyarrow as pa
from dora import Node

node = Node()
Num = 0
for event in node:
    if event["type"] == "INPUT" :
        Num += 1
        node.send_output("plusone", pa.array([Num]))
    elif event["type"] == "STOP" or event["type"] == "INPUT_CLOSED":
        break
