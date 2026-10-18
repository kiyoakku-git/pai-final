import csv
import os
import time

from dora import Node

from common import ROOT, read_json
from scene import in_tray

INSTRUCTION = os.environ.get("INSTRUCTION", "")
CSV = os.path.join(ROOT, "outputs/dora/results.csv")


def main():
    node = Node()
    run_id = time.strftime("%Y%m%d-%H%M%S")
    rows = []
    truth = None
    closed = set()
    for event in node:
        if event["type"] == "INPUT":
            msg = read_json(event)
            if event["id"] == "done":
                truth = msg["truth"]
            elif event["id"] == "detection" and truth is not None:
                label = msg["label"]
                camera_ok = msg["found"] and in_tray(msg["pos"])
                true_ok = in_tray(truth[label])
                rows.append([run_id, INSTRUCTION, label, camera_ok, true_ok])
                truth = None
        elif event["type"] == "INPUT_CLOSED":
            closed.add(event["id"])
            if closed == {"detection", "done"}:
                break
        elif event["type"] == "STOP":
            break

    new_file = not os.path.exists(CSV)
    with open(CSV, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["run", "instruction", "target", "camera_ok", "true_ok"])
        w.writerows(rows)
    print(f"[recorder] wrote {len(rows)} rows to {CSV}", flush=True)


if __name__ == "__main__":
    main()