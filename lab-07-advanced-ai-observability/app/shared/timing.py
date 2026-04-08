import time
from contextlib import contextmanager


class StageTimer:
    def __init__(self) -> None:
        self._start = time.perf_counter()
        self.stages: list[dict] = []

    @contextmanager
    def stage(self, name: str):
        start = time.perf_counter()
        yield
        end = time.perf_counter()
        self.stages.append(
            {
                "name": name,
                "start_ms": round((start - self._start) * 1000, 2),
                "duration_ms": round((end - start) * 1000, 2),
            }
        )

    def total_ms(self) -> float:
        return round((time.perf_counter() - self._start) * 1000, 2)
