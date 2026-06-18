"""
Moduł pętli monitorowania SysmonAgent

Odpowiada za planowanie oraz wykonywanie kolektorów zgodnie
z interwałami zdefiniowanymi przez użytkownika.

Moduł utrzymuje lekki mechanizm timerów, który śledzi moment,
w którym każdy kolektor powinien zostać uruchomiony.
Zebrane zdarzenia są przekazywane do kolejki loggera
w celu asynchronicznego zapisania.
"""

import time
import logger


# Przechowuje znaczniki czasu kolejnego uruchomienia
# poszczególnych kolektorów.
#
# Klucz: nazwa kolektora
# Wartość: czas kolejnego uruchomienia (znacznik UNIX)
timers = {}


def run_loop(
    intervals,
    active_collectors,
    warning_level,
    stop_event,
    statistics,
    container_names,
    socket_client
):
    """
    Uruchamia główną pętlę monitorowania.

    Pętla inicjalizuje timery kolektorów i nieprzerwanie
    sprawdza, czy którykolwiek z nich powinien zostać
    wykonany zgodnie ze skonfigurowanym interwałem.

    Działanie trwa do momentu ustawienia sygnału zatrzymania.

    Argumenty:
        intervals (dict):
            Interwały wykonywania kolektorów wyrażone
            w sekundach.

        active_collectors (dict):
            Mapowanie nazw kolektorów na funkcje kolektorów.

        warning_level (int):
            Próg wykorzystywany przez zdarzenia ostrzegawcze.

        stop_event (threading.Event):
            Obiekt synchronizacyjny wykorzystywany
            do zatrzymania monitorowania.

        statistics:
            Obiekt statystyk wykorzystywany do gromadzenia
            metryk działania aplikacji.

        container_names (list[str]):
            Lista nazw monitorowanych kontenerów.

        socket_client (socket.socket):
            Połączony klient gniazda UNIX wykorzystywany
            do komunikacji z serwerem działającym po stronie hosta.
    """

    declare_timers(active_collectors)

    while not stop_event.is_set():

        collect_and_log(
            intervals,
            active_collectors,
            statistics,
            container_names,
            socket_client
        )

        # Zapobiega aktywnemu oczekiwaniu (busy-waiting)
        # oraz nadmiernemu wykorzystaniu procesora.
        stop_event.wait(0.1)


def collect_and_log(
    intervals,
    active_collectors,
    statistics,
    container_names,
    socket_client
):
    """
    Uruchamia zaplanowane kolektory i przekazuje wygenerowane
    zdarzenia do kolejki loggera.

    Dla każdego kolektora funkcja sprawdza, czy upłynął
    skonfigurowany interwał wykonania. Jeżeli tak,
    kolektor zostaje uruchomiony dla każdego monitorowanego
    kontenera.

    Błędy kolektorów są konwertowane na ustandaryzowane
    zdarzenia błędów i przekazywane do loggera.

    Argumenty:
        intervals (dict):
            Interwały wykonywania kolektorów.

        active_collectors (dict):
            Zarejestrowane funkcje kolektorów.

        statistics:
            Obiekt przechowujący statystyki działania aplikacji.

        container_names (list[str]):
            Kontenery wybrane do monitorowania.

        socket_client (socket.socket):
            Połączony klient gniazda UNIX.
    """

    global timers

    for key, collector in active_collectors.items():

        try:
            current_time = time.time()

            if current_time >= timers[key]:
                timers[key] = timers[key] + intervals[key]
            else:
                continue

        except Exception as error_exception:
            statistics.record_error()

            event = make_error_event(
                error_exception,
                key
            )

            logger.q.put(event, timeout=1)

            continue

        for container in container_names:

            event = collector(
                container,
                socket_client
            )

            logger.q.put(event, timeout=1)


def make_metric_event(metric, value, warning_level):
    """
    Tworzy ustandaryzowane zdarzenie metryki.

    Poziom ważności zdarzenia jest określany automatycznie
    na podstawie skonfigurowanego progu ostrzegawczego.

    Argumenty:
        metric (str):
            Identyfikator metryki.

        value (float | int):
            Zmierzona wartość metryki.

        warning_level (int):
            Próg ostrzegawczy wyrażony w procentach.

    Zwraca:
        dict:
            Sformatowane zdarzenie metryki.
    """

    now = time.time()

    level = (
        "INFO"
        if value < warning_level
        else "WARNING"
    )

    event = {
        "level": level,
        "event": "metric_collected",
        "metric": metric,
        "value": value,
        "unit": "%",
        "created_at": now
    }

    return event


def make_error_event(error_exception, collector_action):
    """
    Tworzy ustandaryzowane zdarzenie błędu kolektora.

    Zdarzenia błędów są generowane zawsze wtedy,
    gdy kolektor napotka wyjątek podczas wykonywania.

    Argumenty:
        error_exception (Exception):
            Przechwycony obiekt wyjątku.

        collector_action (str):
            Identyfikator kolektora powiązanego z błędem.

    Zwraca:
        dict:
            Sformatowane zdarzenie błędu.
    """

    error_type = type(error_exception).__name__
    error_message = str(error_exception)

    now = time.time()

    event = {
        "level": "ERROR",
        "event": "collector_error",
        "action": collector_action,
        "error_type": error_type,
        "error_message": error_message,
        "created_at": now
    }

    return event


def declare_timers(collectors):
    """
    Inicjalizuje timery wykonywania wszystkich aktywnych
    kolektorów.

    Każdy kolektor otrzymuje początkowy znacznik czasu
    równy aktualnemu czasowi systemowemu, co pozwala
    na jego natychmiastowe uruchomienie po starcie aplikacji.

    Argumenty:
        collectors (dict):
            Mapowanie zarejestrowanych kolektorów.
    """

    global timers

    for key, collector in collectors.items():
        timers[key] = time.time()