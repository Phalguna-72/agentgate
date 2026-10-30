import json
import time


def write_audit(entry: dict, path: str = "audit.jsonl") -> None:
    record = {"time": time.time(), **entry}
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")