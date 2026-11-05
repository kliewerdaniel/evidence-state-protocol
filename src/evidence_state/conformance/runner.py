from __future__ import annotations
import json
from pathlib import Path

def run_fixture(fixture, tmp_path):
    # Honest: not yet executing full operations
    return {"id": fixture.get("id"), "passed": False, "reason": "not implemented"}