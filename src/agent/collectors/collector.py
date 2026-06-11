"""
SysmonAgent Collector Module

Provides collector functions responsible for requesting
monitoring data from the host-side server.

Collectors communicate with the server through a UNIX socket
and return parsed monitoring data to the monitoring client.
"""

import json


def get_container_stats(container_name, socket_client):
    """
    Requests filtered Docker container statistics from the host server.

    The function creates a JSON request containing the requested
    action and target container name, sends it through the UNIX
    socket connection and returns the parsed JSON response.

    Args:
        container_name (str):
            Name of the monitored Docker container.

        socket_client (socket.socket):
            Connected UNIX socket client used for communication
            with the host-side server.

    Returns:
        dict:
            Filtered container statistics returned by the server.

    Raises:
        OSError:
            If socket communication fails.

        json.JSONDecodeError:
            If the server response contains invalid JSON data.
    """

    request = {
        "action": "get_stats",
        "container_name": container_name
    }

    message = json.dumps(request).encode() + b"\n"

    socket_client.sendall(message)

    response = socket_client.recv(4096)

    data = json.loads(response.decode())

    return data

