import logger
import time

start_time = time.time()

def start_heartbeat(stop_event, interval):


    while not stop_event.is_set():

        logger.q.put(make_heartbeat_event())



        stop_event.wait(interval)





def make_heartbeat_event():

    event={
        "level" : "INFO",
        "event" : "heartbeat",
        "status": "ok",
        "uptime": round(time.time() - start_time, 2),
        "queue_size": logger.q.qsize()
    }
    return event
