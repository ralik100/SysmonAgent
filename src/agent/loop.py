import cpu
import disc
import ram
import time
import logger


METRICS={
    "cpu_usage" : cpu.get_cpu_usage,
    "ram_usage" : ram.get_ram_usage,
    "disc_usage": disc.get_disc_usage
}

def run():
    """
    timestamp = time of event generated in ISO 8601 + UTC
    level = level of urgency
    event = type of event
    metric = type of metric
    value = integer number between 0 and 100
    unit = %
    """
    file = logger.init()
    while True:
        for (metric, collector) in METRICS.items():
            value=collector()
            event = make_metric_event(metric, value)
            logger.log(event,file)
        time.sleep(5)


def make_metric_event(metric, value):
    level="INFO" if value <70 else "WARNING"
    event={
        "level" : level,
        "event" : "metric_collected",
        "metric": metric,
        "value" : value,
        "unit"  : "%"
    }
    return event