import time
from contextlib import contextmanager


@contextmanager
def clock(print_info: str="Cost", logger=None, line: str='='):

    start_time = time.time()

    yield

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