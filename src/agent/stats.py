import threading
import time
from collections import deque
from datetime import datetime


class Telemetry:
    def __init__(self, lag_window=100):
        self.lock = threading.Lock()


        self.events_processed = 0
        self.errors = 0

        self.lags = deque(maxlen=lag_window)
        self.max_lag = 0.0

        self.start_time = time.time()

    # ---------- UPDATE METHODS ----------

    def record_event(self):
        with self.lock:
            self.events_processed += 1

    def record_error(self):
        with self.lock:
            self.errors += 1

    def record_lag(self, lag):
        with self.lock:
            self.lags.append(lag)

            if lag > self.max_lag:
                self.max_lag = lag

    # ---------- SNAPSHOT ----------

    def snapshot(self, queue_size, queue_capacity):
        with self.lock:
            uptime = time.time() - self.start_time

            if self.lags:
                avg_lag = sum(self.lags) / len(self.lags)
            else:
                avg_lag = 0.0

            eps = self.events_processed / uptime if uptime > 0 else 0.0

            utilization = (
                queue_size / queue_capacity if queue_capacity > 0 else 0.0
            )

            return {
                "level" : "HEARTBEAT",
                "uptime": uptime,

                "performance": {
                    "events_processed": self.events_processed,
                    "events_per_sec": eps,
                    "avg_lag": avg_lag,
                    "max_lag": self.max_lag,
                },

                "queue": {
                    "size": queue_size,
                    "capacity": queue_capacity,
                    "utilization": utilization,
                },

                "errors": {
                    "total": self.errors,
                }
            }