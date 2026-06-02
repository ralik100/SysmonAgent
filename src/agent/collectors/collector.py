import json


def get_container_stats(container_name, socket_client):

    request = {
        "action" : "get_stats",
        "container" : container_name
    }

    message = json.dumps(request).encode() + b"\n"

    socket_client.sendall(message)

    response = socket_client.recv(4096)

    data = json.loads(response.decode())

    return data