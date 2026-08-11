from pathlib import Path
from threading import Lock, current_thread
from time import monotonic


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
