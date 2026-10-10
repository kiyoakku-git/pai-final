"""Turn a short English instruction into the list of objects to move.

Examples
--------
"put the red block in the tray"            -> ["red block"]
"put the red and blue blocks in the tray"  -> ["red block", "blue block"]
"clean up all the blocks"                  -> ["red block", "green block", "blue block"]
"""
import re

COLORS = ["red", "green", "blue"]


def parse_instruction(text, known=None):
    known = known or [f"{c} block" for c in COLORS]
    t = text.lower()
    if re.search(r"\b(all|every|everything|clean up|tidy)\b", t):
        return list(known)
    # keep the order in which the colors are mentioned
    found = sorted(((m.start(), m.group(1)) for m in re.finditer(r"\b(" + "|".join(COLORS) + r")\b", t)))
    targets = []
    for _, color in found:
        name = f"{color} block"
        if name in known and name not in targets:
            targets.append(name)
    return targets
