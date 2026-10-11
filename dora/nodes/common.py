"""Helpers shared by the nodes: make src/ importable and pack/unpack messages."""
import json
import os
import sys

import numpy as np
import pyarrow as pa

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))


def send_json(node, output, data, metadata=None):
    node.send_output(output, pa.array([json.dumps(data)]), metadata or {})


def read_json(event):
    return json.loads(event["value"].to_pylist()[0])


def send_array(node, output, arr, metadata):
    """Send a numpy array; its shape and dtype travel in the metadata."""
    arr = np.ascontiguousarray(arr)
    md = dict(metadata, shape=json.dumps(list(arr.shape)), dtype=str(arr.dtype))
    node.send_output(output, pa.array(arr.ravel()), md)


def read_array(event):
    md = event["metadata"]
    return event["value"].to_numpy().astype(md["dtype"]).reshape(json.loads(md["shape"]))
