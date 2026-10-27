#!/usr/bin/env python3
"""Fail the run when a queue is running low, so GitHub emails you even with Control House closed.

QUEUES="queue.json:12,photos-queue.json:2" means: warn when fewer than 12 / 2 posts are left
(about two days at the current schedule). Standard library only.
"""
import json
import os
import re
import sys


def count(path):
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if path.endswith(".txt"):
        return len([b for b in re.split(r"(?m)^\s*---\s*$", text) if b.strip()])
    return len(json.loads(text)) if text.strip() else 0


low = []
for spec in os.environ["QUEUES"].split(","):
    path, minimum = spec.strip().rsplit(":", 1)
    left = count(path)
    print(f"{path}: {left} left (alert under {minimum})")
    if left < int(minimum):
        low.append(f"{path} has {left} post{'s' if left != 1 else ''} left")
if low:
    print(f"::error::{'; '.join(low)}. Add posts in Control House.")
    sys.exit(1)
