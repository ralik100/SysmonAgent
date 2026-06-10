import time
import logger
import docker
import collectors.collector

timers = {}



def run_loop(intervals, active_collectors, warning_level, stop_event, statistics, container_names, socket_client):
    

    declare_timers(active_collectors)


    while not stop_event.is_set():
        


        collect_and_log(intervals, active_collectors, statistics, container_names, socket_client)

        stop_event.wait(0.1)



"""
def collect_and_log(intervals,active_metrics, warning_level, statistics):

    global timers

    for (metric, collector) in active_metrics.items():

        try:
            current_time = time.time()
            if current_time >= timers[metric]:
                value=collector()
                timers[metric] = timers[metric] + intervals[metric]
            else:
                continue
        except Exception as error_exception:
            statistics.record_error()
            event = make_error_event(error_exception, metric)
            logger.q.put(event, timeout=1)
            continue
        event = make_metric_event(metric, value, warning_level)
        logger.q.put(event, timeout=1)
"""

def collect_and_log(intervals, active_collectors, statistics, container_names, socket_client):

    global timers

    for key, collector in active_collectors.items():

        try:
            current_time = time.time()
            if current_time >= timers[key]:
                
                timers[key] = timers[key] + intervals[key]
            else:
                continue
        except Exception as error_exception:
            statistics.record_error()
            event = make_error_event(error_exception, key)
            logger.q.put(event, timeout=1)
            continue
        for container in container_names:
            event = collector(container, socket_client)

            

            logger.q.put(event, timeout=1)

def make_metric_event(metric, value, warning_level):
    now = time.time()
    level="INFO" if value < warning_level else "WARNING"
    event={
        "level" : level,
        "event" : "metric_collected",
        "metric": metric,
        "value" : value,
        "unit"  : "%",
        "created_at" : now 
    }
    return event

def make_error_event(error_exception, collector_action):
    error_type = type(error_exception).__name__
    error_message = str(error_exception)
    now = time.time()

    event = {
        "level"         : "ERROR",
        "event"         : "collector_error",
        "action"        : collector_action,
        "error_type"    : error_type,
        "error_message" : error_message,
        "created_at" : now 
    }
    return event


def declare_timers(collectors):

    global timers

    

    for key, collector in collectors.items():

        timers[key]=time.time()