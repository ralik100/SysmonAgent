import json
from datetime import datetime

_file = None

def init():
    global _file
    _file = open("log.json","a")

def log(event):
    if _file is None:
        raise RuntimeError("Logger not initialized")
    
    timestamp=get_datetime()
    event["timestamp"] = timestamp
    _file.write(json.dumps(event) + "\n")
    _file.flush()


def get_datetime():
    current_utc_datetime = datetime.utcnow()
    current_utc_iso_datetime = current_utc_datetime.isoformat() + "Z"

    return current_utc_iso_datetime

def close():
    if _file:
        _file.close()