import time
import logger



timers = {
    "cpu_usage" : time.time(),
    "ram_usage" : time.time(),
    "disc_usage": time.time()
}



def run_loop(intervals, active_metrics, warning_level, stop_event):
    

    while not stop_event.is_set():
        


        collect_and_log(intervals, active_metrics, warning_level)

        stop_event.wait(0.1)




def collect_and_log(intervals,active_metrics, warning_level):

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
            event = make_error_event(error_exception, metric)
            logger.q.put(event)
            continue
        event = make_metric_event(metric, value, warning_level)
        logger.q.put(event)


def make_metric_event(metric, value, warning_level):
    level="INFO" if value < warning_level else "WARNING"
    event={
        "level" : level,
        "event" : "metric_collected",
        "metric": metric,
        "value" : value,
        "unit"  : "%"
    }
    return event

def make_error_event(error_exception, metric):
    error_type = type(error_exception).__name__
    error_message = str(error_exception)

    event = {
        "level"         : "ERROR",
        "event"         : "collector_error",
        "metric"        : metric,
        "error_type"    : error_type,
        "error_message" : error_message
    }
    return event
