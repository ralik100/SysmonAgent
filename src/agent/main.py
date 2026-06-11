"""
SysmonAgent Agent Entry Point

This module is responsible for application startup and lifecycle
management.

The agent performs the following tasks:

1. Loads configuration from config.json.
2. Establishes a connection with the host-side server.
3. Initializes the logging subsystem.
4. Starts monitoring and heartbeat threads.
5. Coordinates graceful shutdown of all components.

The module serves as the central orchestration point for the
monitoring client running inside the Docker container.
"""

import loop
import logger
import heartbeat
import json
import collectors.collector
import threading
import stats
import socket


# Maps collector identifiers from configuration files
# to their implementation functions.
COLLECTORS_MAP = {
    "container_stats": collectors.collector.get_container_stats
}


# UNIX socket used for communication with the host server.
SOCKET_PATH = "/tmp/socket/metrics.sock"


def load_config():
    """
    Loads application configuration from config.json.

    The function parses configuration values and creates
    a dictionary containing only collectors enabled by
    the user.

    Returns:
        tuple:
            mode (str)
            intervals (dict)
            active_collectors (dict)
            warning_threshold (int)
            logger_config (dict)
            heartbeat_conf (dict)
            container_names (list[str])

    Raises:
        FileNotFoundError:
            If config.json does not exist.

        json.JSONDecodeError:
            If the configuration file contains invalid JSON.
    """

    with open("config.json", "r") as f:
        config = json.load(f)

    collectors = config["collectors"]
    intervals = config["intervals"]
    warning_threshold = config["warning_threshold"]
    heartbeat_conf = config["heartbeat"]
    logger_config = config["logger"]
    mode = config["mode"]
    container_names = config["monitored_container_names"]

    active_collectors = {}

    for (key, collector) in COLLECTORS_MAP.items():
        if key in collectors:
            active_collectors[key] = collector

    return (
        mode,
        intervals,
        active_collectors,
        warning_threshold,
        logger_config,
        heartbeat_conf,
        container_names
    )


def connect_to_socket():
    """
    Establishes connection to the host-side UNIX socket server.

    Returns:
        socket.socket:
            Connected UNIX socket client.

    Raises:
        OSError:
            If the socket cannot be reached or connection fails.
    """

    socket_client = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM
    )

    print("CONNECTING TO SOCKET...")

    socket_client.connect(SOCKET_PATH)

    print("CONNECTED")

    return socket_client


def disconnect_socket(socket_client):
    """
    Closes an active UNIX socket connection.

    Args:
        socket_client (socket.socket):
            Connected socket instance.
    """

    socket_client.close()


def main():
    """
    Main application entry point.

    Initializes all required subsystems and starts the
    monitoring workflow according to the selected mode.

    Startup sequence:

    1. Create telemetry collector.
    2. Create stop event for thread synchronization.
    3. Load configuration.
    4. Connect to host server.
    5. Initialize logger.
    6. Start logger thread.
    7. Start monitoring loop.
    8. Optionally start heartbeat thread.

    Shutdown sequence:

    1. Stop monitoring threads.
    2. Wait for event queue to be flushed.
    3. Stop logger thread.
    4. Close socket connection.

    Raises:
        ValueError:
            If an unsupported execution mode is configured.
    """

    statistics = stats.Telemetry()

    stop_event = threading.Event()

    (
        mode,
        intervals,
        active_collectors,
        warning_threshold,
        logger_config,
        heartbeat_conf,
        container_names
    ) = load_config()

    heartbeat_enabled = heartbeat_conf["enabled"]

    log_file = logger_config["log_filename"]
    batch_size = logger_config["batchsize"]
    flush_interval = logger_config["flush_interval"]

    socket_client = connect_to_socket()

    logger.init(log_file)

    # Dedicated thread responsible for asynchronous
    # event persistence.
    _logger_thread = threading.Thread(
        target=logger.log,
        args=(
            batch_size,
            flush_interval,
            statistics,
        )
    )

    _logger_thread.start()

    try:

        match mode:

            case "once":

                # Execute enabled collectors once and exit.
                loop.collect_and_log(
                    active_collectors,
                    warning_threshold
                )

            case "loop":

                # Start continuous monitoring loop.
                _loop_thread = threading.Thread(
                    target=loop.run_loop,
                    args=(
                        intervals,
                        active_collectors,
                        warning_threshold,
                        stop_event,
                        statistics,
                        container_names,
                        socket_client,
                    )
                )

                _loop_thread.start()

                # Optional heartbeat subsystem.
                if heartbeat_enabled:

                    heartbeat_interval = heartbeat_conf["interval"]

                    _heartbeat_thread = threading.Thread(
                        target=heartbeat.start_heartbeat,
                        args=(
                            stop_event,
                            heartbeat_interval,
                            statistics,
                        )
                    )

                    _heartbeat_thread.start()

                while _loop_thread.is_alive():
                    _loop_thread.join(timeout=0.5)

            case _:
                raise ValueError("Wrong mode given!")

    except KeyboardInterrupt:

        # Graceful shutdown initiated by the user.
        if mode == "loop":

            stop_event.set()

            _loop_thread.join()

            if heartbeat_enabled:
                _heartbeat_thread.join()

    finally:

        # Wait until all queued events have been written.
        logger.q.join()

        logger.close()

        _logger_thread.join()

        disconnect_socket(socket_client)


if __name__ == "__main__":
    main()