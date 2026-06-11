"""
SysmonAgent Host Server Module

This module provides a secure interface between monitoring
agents and Docker Engine.

The server exposes a UNIX socket used by monitoring clients
running inside Docker containers. Instead of granting direct
access to Docker Engine, all requests are validated and
processed by this dedicated service.

Responsibilities:

- receive monitoring requests,
- communicate with Docker SDK,
- collect container statistics,
- filter raw Docker metrics,
- return normalized monitoring events.

This architecture prevents monitoring containers from
accessing Docker daemon resources directly.
"""

import socket
import os
import json
import docker
import time


# Docker SDK client used for communication with Docker Engine.
docker_client = docker.from_env()


# UNIX socket path shared between server and monitoring agent.
SOCKET_PATH = "/tmp/socket/metrics.sock"


def perform_request(request):
    """
    Processes a monitoring request received from a client.

    The function validates the requested action, retrieves
    the target container, and executes the appropriate
    Docker SDK operation.

    Currently supported actions:

    - get_stats

    Args:
        request (dict):
            Request received through the UNIX socket.

    Returns:
        dict:
            Filtered monitoring event.

    Raises:
        docker.errors.NotFound:
            If the requested container does not exist.

        Exception:
            If an unsupported action is requested.
    """

    command = request["action"]

    container_name = request["container_name"]

    container = docker_client.containers.get(
        container_name
    )

    match command:

        case "get_stats":

            stats = container.stats(
                stream=False
            )

            event = filter_event(stats)

            return event

        case _:
            raise Exception(
                "Wrong request submitted, please check your configuration."
            )


def start_server():
    """
    Creates and initializes the UNIX socket server.

    Startup sequence:

    1. Remove existing socket file if present.
    2. Create UNIX socket.
    3. Bind socket to configured path.
    4. Set socket permissions.
    5. Start listening for connections.

    Returns:
        socket.socket:
            Initialized server socket.
    """

    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM
    )

    server.bind(SOCKET_PATH)

    # Allow communication from Docker containers.
    os.chmod(SOCKET_PATH, 0o777)

    server.listen(0)

    print("SERVER STARTED")

    return server


def close_connection(server):
    """
    Closes the server socket.

    Args:
        server (socket.socket):
            Server socket instance.
    """

    server.close()


def filter_event(stats):
    """
    Converts raw Docker statistics into a normalized
    monitoring event.

    The function extracts only metrics required by
    SysmonAgent and removes unnecessary Docker SDK data.

    Collected metrics:

    - CPU utilization percentage
    - Memory utilization percentage
    - Memory usage in bytes
    - Network RX bytes
    - Network TX bytes

    Args:
        stats (dict):
            Raw Docker statistics returned by
            container.stats(stream=False).

    Returns:
        dict:
            Filtered monitoring event.
    """

    now = time.time()

    # CPU usage difference between two consecutive samples.
    cpu_delta = (
        stats["cpu_stats"]["cpu_usage"]["total_usage"]
        - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    )

    # Host CPU usage difference between samples.
    system_delta = (
        stats["cpu_stats"]["system_cpu_usage"]
        - stats["precpu_stats"]["system_cpu_usage"]
    )

    cpu_percent = 0.0

    if system_delta > 0:

        cpu_percent = (
            cpu_delta
            / system_delta
            * stats["cpu_stats"]["online_cpus"]
            * 100
        )

    # Container memory utilization percentage.
    memory_percent = (
        stats["memory_stats"]["usage"]
        / stats["memory_stats"]["limit"]
        * 100
    )

    filtered_event = {

        # Docker container identifier.
        "container_id":
            stats["id"],

        # Human-readable container name.
        "container_name":
            stats["name"].lstrip("/"),

        # Event severity level.
        "level":
            "INFO",

        # Event type.
        "event":
            "get_stats",

        # CPU utilization percentage.
        "cpu_percent":
            round(cpu_percent, 2),

        # Memory utilization percentage.
        "memory_percent":
            round(memory_percent, 2),

        # Memory consumption in bytes.
        "memory_usage_bytes":
            stats["memory_stats"]["usage"],

        # Total bytes received by container.
        "network_rx_bytes":
            stats["networks"]["eth0"]["rx_bytes"],

        # Total bytes transmitted by container.
        "network_tx_bytes":
            stats["networks"]["eth0"]["tx_bytes"],

        # UNIX timestamp used for lag calculations.
        "created_at":
            now
    }

    return filtered_event


def handle_connections(server):
    """
    Waits for client connections and processes requests.

    The current implementation supports a single connected
    monitoring client. Requests are handled sequentially.

    Communication flow:

    Client
        -> JSON request
        -> UNIX socket

    Server
        -> Docker SDK
        -> filtered event

    Server
        -> JSON response
        -> UNIX socket

    Args:
        server (socket.socket):
            Listening server socket.
    """

    print("Waiting for connection...")

    conn, _ = server.accept()

    print("CLIENT CONNECTED")

    while True:

        request = conn.recv(4096)

        data = json.loads(
            request.decode()
        )

        response = json.dumps(
            perform_request(data)
        ).encode()

        conn.sendall(response)