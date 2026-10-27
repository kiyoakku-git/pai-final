# listener_node.py

from dora import Node

node = Node()
for event in node:
    if event["type"] == "INPUT":
        #print(event["value"].to_pylist()+10)
        print(event["value"].to_pylist()[0]+10)
