"""planner node: instruction -> targets, then look -> pick&place -> look again (retry on failure).

inputs : tick (start), detection (from detector), done (from sim)
outputs: look (json {"req", "label"}), command (json {"req", "action", ...})
"""
import json
import os

from dora import Node

from common import ROOT, read_json, send_json
from instruction import parse_instruction
from scene import BLOCK_SIZE, TRAY_CENTER, TRAY_SLOTS, in_tray

INSTRUCTION = os.environ.get("INSTRUCTION", "put the red block in the tray")
MAX_TRIES = int(os.environ.get("MAX_TRIES", "2"))
LOG = os.path.join(ROOT, os.environ.get("LOG", "outputs/dora/log.json"))


def main():
    node = Node()
    targets = parse_instruction(INSTRUCTION)
    print(f'[planner] "{INSTRUCTION}" -> {targets}', flush=True)
    log = {"instruction": INSTRUCTION, "targets": targets, "results": []}
    state = {"i": 0, "try": 0, "slot": 0, "phase": "idle", "req": 0}

    def look(phase):
        state["req"] += 1
        state["phase"] = phase
        send_json(node, "look", {"req": state["req"], "label": targets[state["i"]]})

    def next_target(success):
        log["results"].append({"target": targets[state["i"]], "success": success, "tries": state["try"]})
        state["i"] += 1
        state["try"] = 0
        if state["i"] < len(targets):
            look("find")
        else:
            finish()

    def finish():
        n_ok = sum(r["success"] for r in log["results"])
        log["summary"] = f"{n_ok}/{len(targets)} objects in the tray"
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "w") as f:
            json.dump(log, f, indent=2)
        print(f"[planner] {log['summary']}", flush=True)
        state["phase"] = "finished"
        send_json(node, "command", {"req": state["req"] + 1, "action": "finish"})

    for event in node:
        if event["type"] == "STOP":
            break
        if event["type"] != "INPUT":
            continue
        if event["id"] == "tick":
            if state["phase"] == "idle":
                if targets:
                    look("find")
                else:
                    finish()
            continue
        msg = read_json(event)
        if msg.get("req") != state["req"] and event["id"] == "detection":
            continue  # stale answer
        name = targets[state["i"]] if state["i"] < len(targets) else None

        if event["id"] == "detection" and state["phase"] == "find":
            if not msg["found"]:
                print(f"[planner] {name}: not found", flush=True)
                next_target(False)
            elif in_tray(msg["pos"]):
                print(f"[planner] {name}: already in the tray", flush=True)
                next_target(True)
            else:
                state["try"] += 1
                dx, dy = TRAY_SLOTS[state["slot"] % len(TRAY_SLOTS)]
                place = [TRAY_CENTER[0] + dx, TRAY_CENTER[1] + dy, BLOCK_SIZE / 2]
                print(f"[planner] {name}: try {state['try']} pick at {msg['pos']}", flush=True)
                state["req"] += 1
                state["phase"] = "moving"
                send_json(node, "command", {"req": state["req"], "action": "pick_place",
                                            "pick": msg["pos"], "place": place})

        elif event["id"] == "done" and state["phase"] == "moving":
            look("check")  # closed loop: look again after acting

        elif event["id"] == "detection" and state["phase"] == "check":
            ok = msg["found"] and in_tray(msg["pos"])
            print(f"[planner] {name}: camera check {'OK' if ok else 'FAILED'}", flush=True)
            if ok:
                state["slot"] += 1
                next_target(True)
            elif state["try"] < MAX_TRIES:
                look("find")  # retry from the current position
            else:
                next_target(False)

        if state["phase"] == "finished":
            break


if __name__ == "__main__":
    main()
