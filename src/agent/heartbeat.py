"""
SysmonAgent Heartbeat Module

Responsible for generating periodic heartbeat events describing
the internal state of the monitoring application.

Heartbeat events provide operational metrics such as queue
utilization, event processing statistics and error counters.
"""

import logger


def start_heartbeat(stop_event, interval, statistics):
    """
    Starts the heartbeat loop.

    The function periodically generates heartbeat events using
    the provided statistics object and places them into the
    logger queue for persistence.

    Execution continues until the stop event is signaled.

    Args:
        stop_event (threading.Event):
            Synchronization object used to stop the heartbeat loop.

        interval (int | float):
            Time between heartbeat events in seconds.

        statistics:
            Statistics provider responsible for generating
            heartbeat snapshots.

    Returns:
        dict:
            Last generated heartbeat event before shutdown.

    Notes:
        Heartbeat events contain information about application
        health, logger queue utilization, throughput and
        accumulated errors.
    """

    while not stop_event.is_set():

        event = statistics.snapshot(
            logger.q.qsize(),
            1000
        )

        logger.q.put(event, timeout=1)

        stop_event.wait(interval)

    return event

