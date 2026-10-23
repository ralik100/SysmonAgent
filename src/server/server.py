"""
Punkt wejściowy serwera SysmonAgent

Moduł pełni rolę punktu startowego dla serwera działającego
po stronie hosta.

Serwer odpowiada za:

- utworzenie gniazda UNIX Socket,
- akceptowanie połączeń od klientów,
- obsługę przychodzących żądań monitorujących,
- pobieranie statystyk Dockera za pomocą Docker SDK,
- zwracanie przefiltrowanych metryk do agentów monitorujących.

Cała niskopoziomowa logika serwera została zaimplementowana
w module server.py. Ten moduł odpowiada jedynie za
inicjalizację i zarządzanie cyklem życia serwera.
"""

import src.server.server_methods as server_methods


def main():
    """
    Uruchamia serwer SysmonAgent działający po stronie hosta.

    Przebieg działania:

    1. Tworzy i inicjalizuje serwer UNIX Socket.
    2. Rozpoczyna nasłuchiwanie połączeń klientów.
    3. Obsługuje przychodzące żądania monitorujące.
    4. Poprawnie zamyka serwer podczas zakończenia pracy.

    Funkcja deleguje wszystkie operacje sieciowe
    do modułu server.
    """

    client = server_methods.start_server()

    server_methods.handle_connections(client)

    server_methods.close_connection(client)


if __name__ == "__main__":
    main()