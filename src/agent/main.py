import loop
import logger
import json
import cpu
import disc
import ram

METRICS={
    "cpu_usage" : cpu.get_cpu_usage,
    "ram_usage" : ram.get_ram_usage,
    "disc_usage": disc.get_disc_usage
}

def load_config():
    with open("config.json","r") as f:
        config=json.load(f)
    metrics = config["metrics"]
    interval = config["interval"]
    warning_threshold = config["warning_threshold"]
    log_filename = config["log_file"]

    active_metrics={}
    for (key, collector) in METRICS.items():
        if key in metrics:
            active_metrics[key]=collector

    return interval, active_metrics, warning_threshold, log_filename

def main():

    interval, active_metrics, warning_threshold, log_file = load_config()

    logger.init(log_file)
    try:
        loop.run(interval, active_metrics, warning_threshold)
    except KeyboardInterrupt:
        pass
    finally:
        logger.close()


if __name__ == "__main__":
    main()

