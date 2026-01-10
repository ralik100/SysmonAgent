import cpu
import disc
import ram
import time
import logger



def run(interval, active_metrics, warning_level):
    """
    timestamp = time of event generated in ISO 8601 + UTC
    level = level of urgency
    event = type of event
    metric = type of metric
    value = integer number between 0 and 100
    unit = %
    """
    while True:
        for (metric, collector) in active_metrics.items():

            value=collector()
            event = make_metric_event(metric, value, warning_level)
            logger.log(event)

        time.sleep(interval)


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