"""
SysmonAgent Server Entry Point

This module serves as the entry point for the host-side server.

The server is responsible for:

- creating a UNIX socket,
- accepting client connections,
- handling incoming monitoring requests,
- collecting Docker statistics through Docker SDK,
- returning filtered metrics to monitoring agents.

All low-level server functionality is implemented in
server.py. This module only initializes the server
lifecycle.
"""

import server



def main():
    """
    Starts the SysmonAgent host server.

    Execution flow:

    1. Create and initialize UNIX socket server.
    2. Start accepting client connections.
    3. Process incoming monitoring requests.
    4. Gracefully close the server on shutdown.

    The function delegates all networking operations
    to the server module.
    """

    client = server.start_server()

    server.handle_connections(client)

    server.close_connection(client)


if __name__ == "__main__":
    main()