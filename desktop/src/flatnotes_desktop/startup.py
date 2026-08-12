from datetime import datetime, timezone
import os
from pathlib import Path
from threading import Lock, current_thread
from time import monotonic


def startup_trace_path(
    data_directory: Path,
    *,
    now: datetime | None = None,
    process_id: int | None = None,
) -> Path:
    timestamp = now or datetime.now(timezone.utc)
    pid = process_id if process_id is not None else os.getpid()
    stamp = timestamp.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    return data_directory / "startup-logs" / f"{stamp}-{pid}.log"


def trace_request(trace, request) -> None:
    trace(f"request:{request.method}:{request.url}")


def trace_response(trace, response) -> None:
    trace(f"response:{response.status_code}:{response.url}")


class StartupTrace:
    """Small, failure-safe timeline for diagnosing packaged startup stalls."""

    def __init__(self, path: Path, clock=monotonic):
        self.path = path
        self.clock = clock
        self.started = clock()
        self.lock = Lock()
        self._write("+0.000s", "trace-opened")

    def __call__(self, event: str) -> None:
        elapsed = self.clock() - self.started
        self._write(f"+{elapsed:.3f}s", event)

    def _write(self, elapsed: str, event: str) -> None:
        try:
            with self.lock:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as output:
                    output.write(f"{elapsed} [{current_thread().name}] {event}\n")
        except OSError:
            # Diagnostics must never prevent the application from starting.
            pass
