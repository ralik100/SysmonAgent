import loop
import logger
import heartbeat
import json
import collectors.collector
import threading
import stats
import socket

COLLECTORS_MAP = {
    "container_stats" : collectors.collector.get_container_stats
}

SOCKET_PATH = "/tmp/metrics.sock"

def load_config():
    with open("config.json","r") as f:
        config=json.load(f)
    collectors = config["collectors"]
    intervals = config["intervals"]
    warning_threshold = config["warning_threshold"]
    heartbeat_conf = config["heartbeat"]
    logger_config = config["logger"]
    mode = config["mode"]
    container_names = config["monitored_container_names"]

    active_collectors={}
    for (key, collector) in COLLECTORS_MAP.items():
        if key in collectors:
            active_collectors[key]=collector

    return mode, intervals, active_collectors, warning_threshold, logger_config, heartbeat_conf, container_names

def connect_to_socket():
    socket_client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    print("CONNECTING TO SOCKET...")

    socket_client.connect(SOCKET_PATH)

    print("CONNECTED")
    
    return socket_client

def disconnect_socket(socket_client):

    socket_client.close()

def main():

    statistics=stats.Telemetry()

    stop_event = threading.Event()

    mode, intervals, active_collectors, warning_threshold, logger_config, heartbeat_conf, container_names = load_config()

    heartbeat_enabled = heartbeat_conf["enabled"]

    log_file = logger_config["log_filename"]
    batch_size = logger_config["batchsize"]
    flush_interval = logger_config["flush_interval"]

    socket_client = connect_to_socket()

    logger.init(log_file)

    _logger_thread = threading.Thread(target=logger.log, args=(batch_size, flush_interval, statistics,))
    _logger_thread.start()
    try:
        match mode:
            case "once":
                loop.collect_and_log(active_collectors, warning_threshold)
            case "loop":
                _loop_thread = threading.Thread(target=loop.run_loop, args=(intervals, active_collectors, warning_threshold, stop_event, statistics, container_names, socket_client,))
                _loop_thread.start()

                if heartbeat_enabled:
                    heartbeat_interval = heartbeat_conf["interval"]
                    _heartbeat_thread = threading.Thread(target=heartbeat.start_heartbeat, args=(stop_event, heartbeat_interval, statistics,))
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
        disconnect_socket(socket_client)

if __name__ == "__main__":
    main()

