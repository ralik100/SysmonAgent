"""
SysmonAgent Monitoring Loop Module

Responsible for scheduling and executing collectors according
to user-defined intervals.

The module maintains a lightweight timer mechanism that tracks
when each collector should be executed. Collected events are
forwarded to the logger queue for asynchronous persistence.
"""

import time
import logger


# Stores next execution timestamps for individual collectors.
# Key: collector name
# Value: next scheduled execution time (UNIX timestamp)
timers = {}


def run_loop(
    intervals,
    active_collectors,
    warning_level,
    stop_event,
    statistics,
    container_names,
    socket_client
):
    """
    Starts the main monitoring loop.

    The loop initializes collector timers and continuously checks
    whether any collector should be executed according to its
    configured interval.

    Execution continues until the stop event is signaled.

    Args:
        intervals (dict):
            Collector execution intervals in seconds.

        active_collectors (dict):
            Mapping of collector names to collector functions.

        warning_level (int):
            Threshold used by warning-generating events.

        stop_event (threading.Event):
            Synchronization object used to stop monitoring.

        statistics:
            Statistics collector used for runtime metrics.

        container_names (list[str]):
            List of monitored container names.

        socket_client (socket.socket):
            Connected UNIX socket client used for communication
            with the host-side server.
    """

    declare_timers(active_collectors)

    while not stop_event.is_set():

        collect_and_log(
            intervals,
            active_collectors,
            statistics,
            container_names,
            socket_client
        )

        # Prevents busy-waiting and excessive CPU consumption.
        stop_event.wait(0.1)


def collect_and_log(
    intervals,
    active_collectors,
    statistics,
    container_names,
    socket_client
):
    """
    Executes scheduled collectors and forwards generated
    events to the logger queue.

    For each collector, the function verifies whether the
    configured execution interval has elapsed. If execution
    is required, the collector is invoked for every monitored
    container.

    Collector failures are converted into standardized error
    events and forwarded to the logger.

    Args:
        intervals (dict):
            Collector execution intervals.

        active_collectors (dict):
            Registered collector functions.

        statistics:
            Runtime statistics collector.

        container_names (list[str]):
            Containers selected for monitoring.

        socket_client (socket.socket):
            Connected UNIX socket client.
    """

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

            event = make_error_event(
                error_exception,
                key
            )

            logger.q.put(event, timeout=1)

            continue

        for container in container_names:

            event = collector(
                container,
                socket_client
            )

            logger.q.put(event, timeout=1)


def make_metric_event(metric, value, warning_level):
    """
    Creates a standardized metric event.

    The event severity level is automatically determined
    based on the configured warning threshold.

    Args:
        metric (str):
            Metric identifier.

        value (float | int):
            Measured metric value.

        warning_level (int):
            Warning threshold percentage.

    Returns:
        dict:
            Formatted metric event.
    """

    now = time.time()

    level = (
        "INFO"
        if value < warning_level
        else "WARNING"
    )

    event = {
        "level": level,
        "event": "metric_collected",
        "metric": metric,
        "value": value,
        "unit": "%",
        "created_at": now
    }

    return event


def make_error_event(error_exception, collector_action):
    """
    Creates a standardized collector error event.

    Error events are generated whenever a collector fails
    during execution.

    Args:
        error_exception (Exception):
            Captured exception instance.

        collector_action (str):
            Collector identifier associated with the failure.

    Returns:
        dict:
            Formatted error event.
    """

    error_type = type(error_exception).__name__
    error_message = str(error_exception)

    now = time.time()

    event = {
        "level": "ERROR",
        "event": "collector_error",
        "action": collector_action,
        "error_type": error_type,
        "error_message": error_message,
        "created_at": now
    }

    return event


def declare_timers(collectors):
    """
    Initializes execution timers for all active collectors.

    Each collector receives an initial execution timestamp
    equal to the current system time, allowing immediate
    execution after startup.

    Args:
        collectors (dict):
            Registered collector mapping.
    """

    global timers

    for key, collector in collectors.items():
        timers[key] = time.time()