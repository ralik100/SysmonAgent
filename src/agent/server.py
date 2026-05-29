import socket
import os

SOCKET_PATH = "/tmp/metrics.sock"

if os.path.exists(SOCKET_PATH):
    os.remove(SOCKET_PATH)

server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

server.bind(SOCKET_PATH)

os.chmod(SOCKET_PATH, 0o777)

server.listen(1)

print("SERVER STARTED")
print("Waiting for connection...")

conn, _ = server.accept()

print("CLIENT CONNECTED")

while True:
    data = conn.recv(1024)

    if not data:
        break

    print(data.decode())