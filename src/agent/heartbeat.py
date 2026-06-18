"""
Moduł Heartbeat SysmonAgent

Odpowiada za generowanie cyklicznych zdarzeń heartbeat opisujących
wewnętrzny stan aplikacji monitorującej.

Zdarzenia heartbeat dostarczają metryk operacyjnych, takich jak
wykorzystanie kolejki, statystyki przetwarzania zdarzeń
oraz liczniki błędów.
"""

import logger


def start_heartbeat(stop_event, interval, statistics):
    """
    Uruchamia pętlę generowania zdarzeń heartbeat.

    Funkcja cyklicznie tworzy zdarzenia heartbeat na podstawie
    danych dostarczanych przez obiekt statystyk, a następnie
    umieszcza je w kolejce loggera w celu zapisania do logów.

    Działanie funkcji trwa do momentu ustawienia sygnału zatrzymania.

    Argumenty:
        stop_event (threading.Event):
            Obiekt synchronizacyjny wykorzystywany do zatrzymania
            pętli heartbeat.

        interval (int | float):
            Czas pomiędzy kolejnymi zdarzeniami heartbeat,
            wyrażony w sekundach.

        statistics:
            Obiekt odpowiedzialny za generowanie migawek
            statystyk wykorzystywanych w zdarzeniach heartbeat.

    Zwraca:
        dict:
            Ostatnie wygenerowane zdarzenie heartbeat
            przed zakończeniem działania funkcji.

    Uwagi:
        Zdarzenia heartbeat zawierają informacje o stanie
        aplikacji, wykorzystaniu kolejki loggera, przepustowości
        przetwarzania zdarzeń oraz liczbie zgromadzonych błędów.
    """

    while not stop_event.is_set():

        event = statistics.snapshot(
            logger.q.qsize(),
            1000
        )

        logger.q.put(event, timeout=1)

        stop_event.wait(interval)

    return event