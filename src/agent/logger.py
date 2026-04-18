import json
from pathlib import Path
import queue
import time
from datetime import datetime

q = queue.Queue(maxsize=1000)

_file = None

def init(log_file):
    global _file
    filepath=Path("/data/output/"+log_file)
    _file = open(filepath,"a")

def log(batch_size, flush_interval, statistics):

    global _file

    batch = []

    while True:
        try:
            event = q.get(timeout=flush_interval)
        except queue.Empty:
            if batch:
                write_batch(batch)
                batch.clear()
            continue


        if event is None:
            q.task_done()
            break
        if _file is None:
            raise RuntimeError("Logger not initialized")
        
        timestamp=get_datetime()
        event["timestamp"] = timestamp

        batch.append(event)
        q.task_done()
        statistics.record_event()

        if event["level"] != "HEARTBEAT":
            now = time.time()
            lag = now - event["created_at"]
            statistics.record_lag(lag)

        if len(batch) >= batch_size:
            write_batch(batch)
            batch.clear()
        


    
    if batch:
        write_batch(batch)
        batch.clear()

    if _file:
        _file.close()
        _file = None


def get_datetime():
    current_utc_datetime = datetime.utcnow()
    current_utc_iso_datetime = current_utc_datetime.isoformat() + "Z"

    return current_utc_iso_datetime

def write_batch(batch):
    global _file

    for event in batch:
        _file.write(json.dumps(event) + "\n")
    _file.flush()

def close():
    q.put(None)