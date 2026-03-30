import loop
import logger
import heartbeat
import json
import collectors.cpu
import collectors.disc
import collectors.ram
import threading

METRICS={
    "cpu_usage" : collectors.cpu.get_cpu_usage,
    "ram_usage" : collectors.ram.get_ram_usage,
    "disc_usage": collectors.disc.get_disc_usage
}

def load_config():
    with open("config.json","r") as f:
        config=json.load(f)
    metrics = config["metrics"]
    intervals = config["intervals"]
    warning_threshold = config["warning_threshold"]
    heartbeat_conf = config["heartbeat"]
    log_filename = config["log_file"]
    mode = config["mode"]

    active_metrics={}
    for (key, collector) in METRICS.items():
        if key in metrics:
            active_metrics[key]=collector

    return mode, intervals, active_metrics, warning_threshold, log_filename, heartbeat_conf

def main():

    stop_event = threading.Event()

    mode, intervals, active_metrics, warning_threshold, log_file, heartbeat_conf= load_config()

    heartbeat_enabled = heartbeat_conf["enabled"]

    logger.init(log_file)

    _logger_thread = threading.Thread(target=logger.log)
    _logger_thread.start()
    try:
        match mode:
            case "once":
                loop.collect_and_log(active_metrics, warning_threshold)
            case "loop":
                _loop_thread = threading.Thread(target=loop.run_loop, args=(intervals, active_metrics, warning_threshold, stop_event,))
                _loop_thread.start()

                if heartbeat_enabled:
                    heartbeat_interval = heartbeat_conf["interval"]
                    _heartbeat_thread = threading.Thread(target=heartbeat.start_heartbeat, args=(stop_event, heartbeat_interval,))
                    _heartbeat_thread.start()

                while _loop_thread.is_alive():
                    _loop_thread.join(timeout=0.5)
            case _:
                raise ValueError("Wrong mode given!")
    except KeyboardInterrupt:
        if mode == "loop":
            stop_event.set()
            _loop_thread.join()
            if heartbeat_enabled:
                _heartbeat_thread.join()
    finally:
        logger.q.join()
        logger.close()
        _logger_thread.join()

if __name__ == "__main__":
    main()

