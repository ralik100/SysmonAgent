import cpu
import disc
import ram
import time
import logger

end = False

def run_loop(interval, active_metrics, warning_level):

    while True:
        
        if end:
            break

        collect_and_log(active_metrics, warning_level)

        time.sleep(interval)




def collect_and_log(active_metrics, warning_level):
    for (metric, collector) in active_metrics.items():

        try:
            value=collector()
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

def end_loop():

    global end
    end = True