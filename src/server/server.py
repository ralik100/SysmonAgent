import socket
import os
import json
import docker
import time

docker_client = docker.from_env()

SOCKET_PATH = "/tmp/socket/metrics.sock"

def perform_request(request):



    command = request["action"]
    container_name = request["container_name"]
    container = docker_client.containers.get(container_name)

    match command:
        case "get_stats":
            stats = container.stats(stream=False)

            event = filter_event(stats)
            return event
        case _:
            raise Exception("Wrong request submitted, please check your configuration.")

def start_server():

    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    server.bind(SOCKET_PATH)

    os.chmod(SOCKET_PATH, 0o777)

    server.listen(0)

    print("SERVER STARTED")

    return server

def close_connection(server):
    server.close()

def filter_event(stats):

    now = time.time()

    cpu_delta = (
        stats["cpu_stats"]["cpu_usage"]["total_usage"]
        - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    )

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

    memory_percent = (
        stats["memory_stats"]["usage"]
        / stats["memory_stats"]["limit"]
        * 100
    )

    filtered_event = {
        "container_id":
            stats["id"],

        "container_name":
            stats["name"].lstrip("/"),

        "level":
            "INFO",

        "event":
            "get_stats",

        "cpu_percent":
            round(cpu_percent, 2),

        "memory_percent":
            round(memory_percent, 2),

        "memory_usage_bytes":
            stats["memory_stats"]["usage"],

        "network_rx_bytes":
            stats["networks"]["eth0"]["rx_bytes"],

        "network_tx_bytes":
            stats["networks"]["eth0"]["tx_bytes"],

        "created_at":
            now
    }
    return filtered_event


def handle_connections(server):

    print("Waiting for connection...")

    conn, _ = server.accept()

    print("CLIENT CONNECTED")

    while True:

        request = conn.recv(4096)

        data = json.loads(request.decode())


        response = json.dumps(perform_request(data)).encode()

        conn.sendall(response)