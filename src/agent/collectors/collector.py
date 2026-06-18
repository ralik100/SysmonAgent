"""
Moduł kolektora SysmonAgent

Udostępnia funkcje kolektorów odpowiedzialne za pobieranie
danych monitorujących z serwera działającego po stronie hosta.

Kolektory komunikują się z serwerem za pomocą gniazda UNIX
i zwracają przetworzone dane monitorujące do klienta monitoringu.
"""

import json


def get_container_stats(container_name, socket_client):
    """
    Pobiera przefiltrowane statystyki kontenera Docker z serwera hosta.

    Funkcja tworzy żądanie JSON zawierające nazwę wykonywanej
    akcji oraz nazwę monitorowanego kontenera, wysyła je przez
    połączenie UNIX Socket, a następnie zwraca sparsowaną
    odpowiedź otrzymaną od serwera.

    Argumenty:
        container_name (str):
            Nazwa monitorowanego kontenera Docker.

        socket_client (socket.socket):
            Połączony klient gniazda UNIX wykorzystywany
            do komunikacji z serwerem działającym po stronie hosta.

    Zwraca:
        dict:
            Przefiltrowane statystyki kontenera zwrócone przez serwer.

    Wyjątki:
        OSError:
            Występuje w przypadku błędu komunikacji przez gniazdo.

        json.JSONDecodeError:
            Występuje, gdy odpowiedź serwera zawiera niepoprawne dane JSON.
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