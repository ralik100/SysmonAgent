import socket
import os
import json
import docker

docker_client = docker.from_env()

SOCKET_PATH = "/tmp/metrics.sock"

def perform_request(request):

    action = request[action]
    container_name = request[container_name]
    container = docker_client.containers.get(container_name)

    match action:
        case "get_stats":
            stats = container.stats(stream=False)
            return stats
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


def handle_connections(server):

    print("Waiting for connection...")

    conn, _ = server.accept()

    print("CLIENT CONNECTED")

    while True:

        request = conn.recv(4096)

        data = json.loads(request.decode())

        response = json.dumps(perform_request(request)).encode()

        conn.sendall(response)