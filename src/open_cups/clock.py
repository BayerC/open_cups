import os
import time

_START_REAL_TIME = time.time()
TIME_SCALE = float(os.environ.get("TIME_SCALE", "1.0"))


def now() -> float:
    """Return current time, scaled by TIME_SCALE factor."""
    elapsed_real = time.time() - _START_REAL_TIME
    return _START_REAL_TIME + elapsed_real * TIME_SCALE
