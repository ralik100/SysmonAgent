import logger
import time

start_time = time.time()

def start_heartbeat(stop_event, interval, statistics):



    while not stop_event.is_set():


        event = statistics.snapshot(logger.q.qsize(), 1000)

        logger.q.put(event, timeout=1)



        stop_event.wait(interval)


    return event
