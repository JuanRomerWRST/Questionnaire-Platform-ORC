import time
from collections import defaultdict


class StageTimer:
    def __init__(self) -> None:
        self.started = time.perf_counter()
        self.durations: dict[str, float] = defaultdict(float)

    def stage(self, name: str):
        return _Stage(self, name)

    def total_ms(self) -> float:
        return (time.perf_counter() - self.started) * 1000


class _Stage:
    def __init__(self, timer: StageTimer, name: str) -> None:
        self._timer = timer
        self._name = name
        self._mark = 0.0

    def __enter__(self) -> "_Stage":
        self._mark = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        elapsed = (time.perf_counter() - self._mark) * 1000
        self._timer.durations[self._name] += elapsed
