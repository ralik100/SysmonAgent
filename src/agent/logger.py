"""
Moduł loggera SysmonAgent

Odpowiada za asynchroniczny zapis zdarzeń.

Zdarzenia generowane przez kolektory oraz wątek heartbeat są
najpierw umieszczane w kolejce znajdującej się w pamięci.
Dedykowany wątek loggera odczytuje zdarzenia z kolejki,
uzupełnia je o znaczniki czasu i zapisuje na dysku
w konfigurowalnych paczkach.

Takie podejście ogranicza liczbę operacji wejścia/wyjścia
na dysku oraz zapobiega blokowaniu procesu monitorowania
przez operacje zapisu do systemu plików.
"""

import json
from pathlib import Path
import queue
import time
from datetime import datetime
import os


# Współdzielona kolejka zdarzeń wykorzystywana przez kolektory,
# heartbeat oraz logger. Kolejka pełni rolę bufora pomiędzy
# producentami zdarzeń a warstwą ich trwałego zapisu.
q = queue.Queue(maxsize=1000)

# Uchwyt do pliku wykorzystywany przez wątek loggera.
_file = None


def init(log_file):
    """
    Inicjalizuje podsystem logowania.

    Tworzy katalog wyjściowy, jeśli jeszcze nie istnieje,
    a następnie otwiera skonfigurowany plik logów
    w trybie dopisywania danych.

    Argumenty:
        log_file (str):
            Nazwa pliku logów.

    Wyjątki:
        OSError:
            Występuje, jeśli nie można utworzyć katalogu
            lub pliku logów.
    """

    global _file

    filepath = Path("/output")

    try:
        os.mkdir(filepath)
        print("Path created successfully")
    except FileExistsError:
        print(f"{filepath} already exists")

    filepath = Path("/output") / log_file

    _file = open(filepath, "a")


def log(batch_size, flush_interval, statistics):
    """
    Główna pętla loggera.

    Odczytuje zdarzenia z kolejki, dodaje znaczniki czasu,
    aktualizuje statystyki wydajności oraz zapisuje zdarzenia
    do pliku w paczkach.

    Zapis następuje gdy:
    - osiągnięto rozmiar paczki określony przez batch_size,
    - upłynął czas flush_interval,
    - zainicjowano zamknięcie loggera.

    Argumenty:
        batch_size (int):
            Maksymalna liczba zdarzeń zapisywanych
            podczas jednego cyklu zapisu.

        flush_interval (int | float):
            Maksymalny czas pomiędzy kolejnymi zapisami
            wyrażony w sekundach.

        statistics:
            Obiekt statystyk wykorzystywany do generowania
            metryk heartbeat.

    Wyjątki:
        RuntimeError:
            Występuje, jeśli logger nie został wcześniej
            zainicjalizowany.
    """

    global _file

    batch = []

    while True:
        try:
            event = q.get(timeout=flush_interval)

        except queue.Empty:
            if batch:
                write_batch(batch)
                batch.clear()

            continue

        if event is None:
            q.task_done()
            break

        if _file is None:
            raise RuntimeError("Logger not initialized")

        timestamp = get_datetime()
        event["timestamp"] = timestamp

        batch.append(event)

        q.task_done()

        statistics.record_event()

        # Zdarzenia heartbeat nie zawierają znacznika czasu
        # utworzenia wykorzystywanego do pomiaru opóźnień.
        if event["level"] != "HEARTBEAT":
            now = time.time()
            lag = now - event["created_at"]
            statistics.record_lag(lag)

        if len(batch) >= batch_size:
            write_batch(batch)
            batch.clear()

    # Zapisuje pozostałe zdarzenia przed zamknięciem aplikacji.
    if batch:
        write_batch(batch)
        batch.clear()

    # Zamyka plik logów podczas poprawnego zakończenia działania.
    if _file:
        _file.close()
        _file = None


def get_datetime():
    """
    Zwraca aktualny znacznik czasu UTC w formacie ISO-8601.

    Zwraca:
        str:
            Aktualny czas UTC zakończony sufiksem „Z”.
    """

    current_utc_datetime = datetime.utcnow()
    current_utc_iso_datetime = current_utc_datetime.isoformat() + "Z"

    return current_utc_iso_datetime


def write_batch(batch):
    """
    Zapisuje paczkę zdarzeń do pliku logów.

    Każde zdarzenie jest serializowane do formatu JSON
    i zapisywane jako osobna linia w pliku.

    Argumenty:
        batch (list[dict]):
            Kolekcja zdarzeń przeznaczonych do zapisania.
    """

    global _file

    for event in batch:
        _file.write(json.dumps(event) + "\n")

    _file.flush()


def close():
    """
    Inicjuje bezpieczne zamknięcie loggera.

    Do kolejki zostaje dodana wartość specjalna (sentinel).
    Po jej odebraniu przez wątek loggera pętla logowania
    kończy działanie po zapisaniu wszystkich oczekujących
    zdarzeń.
    """

    q.put(None)