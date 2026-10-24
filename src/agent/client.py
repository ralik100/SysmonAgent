"""
SysmonAgent – Główny punkt wejścia agenta monitorującego

Moduł odpowiada za uruchamianie aplikacji oraz zarządzanie jej
cyklem życia.

Agent wykonuje następujące zadania:

1. Wczytuje konfigurację z pliku config.json.
2. Nawiązuje połączenie z serwerem działającym po stronie hosta.
3. Inicjalizuje system logowania.
4. Uruchamia wątki monitorowania oraz heartbeat.
5. Koordynuje poprawne zamykanie wszystkich komponentów.

Moduł pełni rolę centralnego punktu orkiestracji dla klienta
monitorującego uruchamianego wewnątrz kontenera Docker.
"""

import loop
import logger
import heartbeat
import json
import collectors.collector
import threading
import stats
import socket
import os


# Mapowanie identyfikatorów kolektorów z pliku konfiguracji
# na odpowiadające im funkcje implementacyjne.
COLLECTORS_MAP = {
    "container_stats": collectors.collector.get_container_stats
}


# Ścieżka do gniazda UNIX wykorzystywanego do komunikacji
# z serwerem działającym po stronie hosta.
SOCKET_PATH = "/tmp/socket/metrics.sock"





def connect_to_socket():
    """
    Nawiązuje połączenie z serwerem wykorzystującym gniazdo UNIX.

    Zwraca:
        socket.socket:
            Połączony klient gniazda UNIX.

    Wyjątki:
        OSError:
            Jeśli połączenie z gniazdem nie może zostać
            nawiązane lub serwer jest niedostępny.
    """

    socket_client = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM
    )

    print("CONNECTING TO SOCKET...")

    socket_client.connect(SOCKET_PATH)

    print("CONNECTED")

    return socket_client


def disconnect_socket(socket_client):
    """
    Zamyka aktywne połączenie z gniazdem UNIX.

    Argumenty:
        socket_client (socket.socket):
            Instancja połączonego gniazda.
    """

    socket_client.close()


def main(mode : str, interval_configuration : dict, collectors_configuration : list[str], warning_threshold : int, logging_configuration : dict, heartbeat_configuration : dict, container_names : list[str], environment_variables : dict):
    """
    Główny punkt wejścia aplikacji.

    Inicjalizuje wszystkie wymagane podsystemy oraz uruchamia
    proces monitorowania zgodnie z wybranym trybem pracy.

    Sekwencja uruchamiania:

    1. Utworzenie obiektu telemetrycznego.
    2. Utworzenie zdarzenia synchronizacyjnego stop_event.
    3. Wczytanie konfiguracji.
    4. Nawiązanie połączenia z serwerem hosta.
    5. Inicjalizacja loggera.
    6. Uruchomienie wątku loggera.
    7. Uruchomienie pętli monitorującej.
    8. Opcjonalne uruchomienie wątku heartbeat.

    Sekwencja zamykania:

    1. Zatrzymanie wątków monitorujących.
    2. Oczekiwanie na opróżnienie kolejki zdarzeń.
    3. Zatrzymanie wątku loggera.
    4. Zamknięcie połączenia z gniazdem UNIX.

    Wyjątki:
        ValueError:
            Jeśli skonfigurowano nieobsługiwany tryb działania.
    """

    

    statistics = stats.Telemetry()

    stop_event = threading.Event()


    socket_client = connect_to_socket()

    logger.init(log_file, log_file_path)

    # Dedykowany wątek odpowiedzialny za asynchroniczny
    # zapis zdarzeń do pliku.
    _logger_thread = threading.Thread(
        target=logger.log,
        args=(
            batch_size,
            flush_interval,
            statistics,
        )
    )

    _logger_thread.start()

    try:

        match mode:

            case "once":

                # Jednorazowe wykonanie aktywnych kolektorów
                # i zakończenie działania aplikacji.
                loop.collect_and_log(
                    active_collectors,
                    warning_threshold
                )

            case "loop":

                # Uruchomienie ciągłej pętli monitorowania.
                _loop_thread = threading.Thread(
                    target=loop.run_loop,
                    args=(
                        intervals,
                        active_collectors,
                        warning_threshold,
                        stop_event,
                        statistics,
                        container_names,
                        socket_client,
                    )
                )

                _loop_thread.start()

                # Opcjonalne uruchomienie mechanizmu heartbeat.
                if heartbeat_enabled:

                    heartbeat_interval = heartbeat_conf["interval"]

                    _heartbeat_thread = threading.Thread(
                        target=heartbeat.start_heartbeat,
                        args=(
                            stop_event,
                            heartbeat_interval,
                            statistics,
                        )
                    )

                    _heartbeat_thread.start()

                while _loop_thread.is_alive():
                    _loop_thread.join(timeout=0.5)

            case _:
                raise ValueError("Wrong mode given!")

    except KeyboardInterrupt:

        # Poprawne zamknięcie aplikacji po przerwaniu
        # działania przez użytkownika.
        if mode == "loop":

            stop_event.set()

            _loop_thread.join()

            if heartbeat_enabled:
                _heartbeat_thread.join()

    finally:

        # Oczekiwanie na zapis wszystkich zdarzeń znajdujących
        # się jeszcze w kolejce loggera.
        logger.q.join()

        logger.close()

        _logger_thread.join()

        disconnect_socket(socket_client)

if __name__ == "__main__":
    main()