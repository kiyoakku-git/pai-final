"""Small helpers shared by the scripts."""
import numpy as np


def to_np(x):
    """Convert a Genesis output (torch tensor on any device, incl. Apple MPS) or array-like to a float numpy array."""
    if hasattr(x, "detach"):
        x = x.detach().cpu().numpy()
    return np.asarray(x, dtype=float)
