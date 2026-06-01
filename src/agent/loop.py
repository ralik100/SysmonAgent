import time
import logger
import docker


timers = {}

docker_client=docker.from_env()


def run_loop(intervals, active_metrics, warning_level, stop_event, statistics, container_names):
    

    monitored_containers = prepare_container_list(container_names)

    declare_timers(monitored_containers)

    while not stop_event.is_set():
        


        collect_and_log(intervals, active_metrics, warning_level, statistics, monitored_containers)

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

def collect_and_log(statistics, container_names):

    global timers

    for container in container_names:

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

def make_error_event(error_exception, metric):
    error_type = type(error_exception).__name__
    error_message = str(error_exception)
    now = time.time()

    event = {
        "level"         : "ERROR",
        "event"         : "collector_error",
        "metric"        : metric,
        "error_type"    : error_type,
        "error_message" : error_message,
        "created_at" : now 
    }
    return event


def prepare_container_list(container_names):

    global docker_client

    container_object_list=[]

    containers=docker_client.containers.list()
    for container in containers:
        if container.name in container_names:
            container_object_list.append(container)
    return container_object_list

def declare_timers(containers):

    global timers

    for container in containers:
        timers[container]=time.time()