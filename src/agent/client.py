import socket

SOCKET_PATH = "/tmp/metrics.sock"

client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

print("CONNECTING...")

client.connect(SOCKET_PATH)

print("CONNECTED")

client.sendall(b"hello from container")

client.close()