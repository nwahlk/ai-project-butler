from time import perf_counter


def now_ms() -> float:
    return perf_counter() * 1000


def elapsed_ms(start_ms: float) -> float:
    return now_ms() - start_ms
