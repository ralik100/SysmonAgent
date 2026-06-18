"""
Moduł Telemetrii SysmonAgent

Udostępnia statystyki działania aplikacji wykorzystywane przez
mechanizm heartbeat.

Klasa Telemetry gromadzi informacje dotyczące:

- liczby przetworzonych zdarzeń,
- błędów aplikacji,
- opóźnień przetwarzania zdarzeń,
- wykorzystania kolejki,
- czasu działania aplikacji.

Zebrane metryki są okresowo udostępniane w zdarzeniach heartbeat,
co pozwala administratorom monitorować stan i wydajność samego
systemu monitorującego.
"""

import threading
import time
from collections import deque


class Telemetry:
    """
    Bezpieczny wielowątkowo kolektor statystyk działania aplikacji.

    Klasa agreguje metryki operacyjne generowane przez różne
    komponenty systemu.

    Statystyki są na bieżąco aktualizowane podczas działania
    aplikacji i okresowo eksportowane w postaci zdarzeń heartbeat.

    Atrybuty:
        lock (threading.Lock):
            Mechanizm synchronizacji chroniący współdzielony stan.

        events_processed (int):
            Całkowita liczba przetworzonych zdarzeń.

        errors (int):
            Całkowita liczba błędów występujących podczas działania.

        lags (deque):
            Bufor cykliczny przechowujący ostatnie pomiary
            opóźnień przetwarzania zdarzeń.

        max_lag (float):
            Największe zaobserwowane opóźnienie przetwarzania.

        start_time (float):
            Znacznik czasu uruchomienia aplikacji.
    """

    def __init__(self, lag_window=100):
        """
        Tworzy nowy kolektor statystyk działania aplikacji.

        Args:
            lag_window (int):
                Maksymalna liczba ostatnich pomiarów opóźnień
                przechowywanych do obliczania średniego opóźnienia.
        """

        self.lock = threading.Lock()

        self.events_processed = 0
        self.errors = 0

        # Przechowuje ostatnie opóźnienia przetwarzania zdarzeń.
        self.lags = deque(maxlen=lag_window)

        # Największe opóźnienie zaobserwowane od uruchomienia.
        self.max_lag = 0.0

        # Znacznik czasu uruchomienia aplikacji.
        self.start_time = time.time()

    # ---------- METODY AKTUALIZACJI ----------

    def record_event(self):
        """
        Rejestruje poprawnie przetworzone zdarzenie.

        Metoda wywoływana przez logger po przyjęciu zdarzenia
        do dalszego przetwarzania.
        """

        with self.lock:
            self.events_processed += 1

    def record_error(self):
        """
        Rejestruje błąd aplikacji.

        Metoda wywoływana zawsze wtedy, gdy podczas działania
        kolektora lub innego monitorowanego komponentu wystąpi wyjątek.
        """

        with self.lock:
            self.errors += 1

    def record_lag(self, lag):
        """
        Rejestruje opóźnienie przetwarzania zdarzenia.

        Opóźnienie definiowane jest jako różnica czasu pomiędzy
        utworzeniem zdarzenia a jego zapisaniem przez logger.

        Args:
            lag (float):
                Opóźnienie przetwarzania wyrażone w sekundach.
        """

        with self.lock:

            self.lags.append(lag)

            if lag > self.max_lag:
                self.max_lag = lag

    # ---------- MIGAWKA STATYSTYK ----------

    def snapshot(self, queue_size, queue_capacity):
        """
        Tworzy migawkę heartbeat zawierającą aktualne statystyki
        działania aplikacji.

        Zwrócona struktura jest bezpośrednio wykorzystywana przez
        mechanizm heartbeat, a następnie zapisywana przez logger.

        Args:
            queue_size (int):
                Aktualna liczba zdarzeń oczekujących w kolejce.

            queue_capacity (int):
                Maksymalna pojemność kolejki.

        Returns:
            dict:
                Kompletne zdarzenie heartbeat zawierające:

                - informacje o czasie działania,
                - metryki wydajności,
                - statystyki kolejki,
                - statystyki błędów.
        """

        with self.lock:

            # Czas, jaki upłynął od uruchomienia aplikacji.
            uptime = time.time() - self.start_time

            # Średnie opóźnienie obliczane na podstawie
            # ostatnich zarejestrowanych pomiarów.
            if self.lags:
                avg_lag = sum(self.lags) / len(self.lags)
            else:
                avg_lag = 0.0

            # Średnia przepustowość przetwarzania zdarzeń.
            eps = (
                self.events_processed / uptime
                if uptime > 0
                else 0.0
            )

            # Stopień wykorzystania kolejki.
            utilization = (
                queue_size / queue_capacity
                if queue_capacity > 0
                else 0.0
            )

            return {
                "level": "HEARTBEAT",

                # Liczba sekund od uruchomienia aplikacji.
                "uptime": uptime,

                "performance": {

                    # Łączna liczba przetworzonych zdarzeń.
                    "events_processed":
                        self.events_processed,

                    # Średnia liczba zdarzeń przetwarzanych na sekundę.
                    "events_per_sec":
                        eps,

                    # Średnie zaobserwowane opóźnienie zdarzeń.
                    "avg_lag":
                        avg_lag,

                    # Największe zaobserwowane opóźnienie zdarzeń.
                    "max_lag":
                        self.max_lag,
                },

                "queue": {

                    # Aktualny rozmiar kolejki.
                    "size":
                        queue_size,

                    # Maksymalna pojemność kolejki.
                    "capacity":
                        queue_capacity,

                    # Współczynnik wykorzystania kolejki.
                    "utilization":
                        utilization,
                },

                "errors": {

                    # Całkowita liczba błędów wykrytych
                    # od momentu uruchomienia aplikacji.
                    "total":
                        self.errors,
                }
            }