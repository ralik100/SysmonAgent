import json
import queue
from datetime import datetime

q = queue.Queue()

_file = None

def init(log_file):
    global _file
    _file = open(log_file,"a")

def log():
    while True:
        event = q.get()

        if event is None:
            q.task_done()
            break
        if _file is None:
            raise RuntimeError("Logger not initialized")
        
        timestamp=get_datetime()
        event["timestamp"] = timestamp
        _file.write(json.dumps(event) + "\n")
        _file.flush()

        q.task_done()
    
    if _file:
        _file.close()
        _file = None


def get_datetime():
    current_utc_datetime = datetime.utcnow()
    current_utc_iso_datetime = current_utc_datetime.isoformat() + "Z"

    return current_utc_iso_datetime

def close():
    q.put(None)