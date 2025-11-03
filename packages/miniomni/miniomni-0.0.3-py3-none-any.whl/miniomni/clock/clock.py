import time
from contextlib import contextmanager
from functools import wraps

@contextmanager
def clock_ctx(print_info: str="Cost", logger=None, line: str='='):

    start_time = time.time()

    yield lambda digits=3: round(time.time() - start_time, digits)

    end_time = time.time()
    cost = end_time - start_time

    if line:
        print(line * 25 + " Clock Info " + line * 25)
    if logger:
        logger.info(f"{print_info}: {cost: .3f}s")
    else:
        print(f"{print_info}: {cost: .3f}s")
    if line:
        print(line * 62)

def clock(print_info: str = "Cost", logger=None, line: str = '='):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()

            cost = end_time - start_time

            if line:
                print(line * 25 + " Clock Info " + line * 25)
            if logger:
                logger.info(f"{print_info}: {cost:.3f}s")
            else:
                print(f"{print_info}: {cost:.3f}s")
            if line:
                print(line * 62)

            return result, round(cost, 3)
        return wrapper
    return decorator