import server



SOCKET_PATH = "/tmp/metrics.sock"





def main():

    client = server.start_server()

    server.handle_connections(client)

    server.close_connection(client)

if __name__ == "__main__":
    main()