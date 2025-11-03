import cProfile
import pstats
from contextlib import ContextDecorator
from functools import wraps
import io

class Profiler(ContextDecorator):
    def __init__(self, name="Profiler", sort_by="cumtime", top=10):
        """
        name: 输出标题
        sort_by: 排序字段，可选 'cumtime', 'tottime', 'ncalls'
        top: 打印前 N 条耗时最多的函数
        """
        self.name = name
        self.sort_by = sort_by
        self.top = top
        self.prof = cProfile.Profile()
        self._stats = None

    # ===== 上下文管理器 =====
    def __enter__(self):
        self.prof.enable()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.prof.disable()
        self._print_stats()

    # ===== 装饰器 =====
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.prof.enable()
            result = func(*args, **kwargs)
            self.prof.disable()
            self._print_stats()
            return result
        return wrapper

    # ===== 内部函数：打印汇总 =====
    def _print_stats(self):
        s = io.StringIO()
        ps = pstats.Stats(self.prof, stream=s).sort_stats(self.sort_by)
        ps.print_stats(self.top)
        print(f"\n{'='*10} {self.name} Summary {'='*10}\n")
        print(s.getvalue())

if __name__ == "__main__":
    @Profiler(name="Module Profiler")
    def task():
        sum([i**2 for i in range(10000)])
        for _ in range(5000):
            pass
    task()

    with Profiler(name="Block Profiler"):
        sum([i**2 for i in range(10000)])
        for _ in range(5000):
            pass