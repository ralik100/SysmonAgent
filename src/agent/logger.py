import json
from datetime import datetime

def init():
    file=open("log.json","a")
    return file

def log(event, file):
    timestamp=get_datetime()
    event["timestamp"] = timestamp
    file.write(json.dumps(event) + "\n")

def get_datetime():
    current_utc_datetime = datetime.utcnow()
    current_utc_iso_datetime = current_utc_datetime.isoformat()

    return current_utc_iso_datetime