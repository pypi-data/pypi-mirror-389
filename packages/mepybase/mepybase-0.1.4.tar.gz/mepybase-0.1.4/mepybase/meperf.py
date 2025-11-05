import time
import functools
from typing import Callable, Dict, Optional
from easylog import EasyLogManager
import os

# 彩色输出
COLORS = {
    "green": "\033[92m",
    "yellow": "\033[93m",
    "cyan": "\033[96m",
    "magenta": "\033[95m",
    "reset": "\033[0m",
}


class PerfStat:
    """保存函数性能统计信息"""

    def __init__(self):
        self.count: int = 0
        self.total_time: float = 0.0
        self.max_time: float = 0.0

    def update(self, elapsed: float) -> None:
        self.count += 1
        self.total_time += elapsed
        if elapsed > self.max_time:
            self.max_time = elapsed

    @property
    def avg_time(self) -> float:
        return self.total_time / self.count if self.count > 0 else 0.0


_perf_stats: Dict[str, PerfStat] = {}


def perf(
    func: Callable = None,
    *,
    log_obj: Optional[EasyLogManager] = None,
    log_file: str = "perf.log",
    log_folder: str = "/tmp/perf_logs",
    color: str = "cyan",
):
    """
    装饰器：
    1. 可以直接使用 @perf
    2. 可以 new_perf = perf(log_file=..., log_folder=..., color=...) 后 @new_perf
    3. 可以传入 log_obj 外部 logger
    """

    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                name = fn.__qualname__
                stat = _perf_stats.setdefault(name, PerfStat())
                stat.update(elapsed)

                # 确定使用的 logger
                if log_obj:
                    active_logger = log_obj
                else:
                    os.makedirs(log_folder, exist_ok=True)
                    active_logger = EasyLogManager.get_logger(
                        name="perf",
                        log_file=log_file,
                        log_folder=log_folder,
                        level="DEBUG",
                    )

                color_code = COLORS.get(color, COLORS["reset"])
                reset = COLORS["reset"]

                active_logger.info(
                    f"{color_code}[PERF] {name} | 本次: {elapsed:.6f}s | "
                    f"平均: {stat.avg_time:.6f}s | 最大: {stat.max_time:.6f}s | "
                    f"总耗时: {stat.total_time:.6f}s | 调用: {stat.count}次{reset}"
                )

        return wrapper

    return decorator(func) if func else decorator


def get_perf_stats() -> Dict[str, PerfStat]:
    return _perf_stats


# ------------------ 测试案例 ------------------
if __name__ == "__main__":
    import random

    print("===== 测试 1: 默认内部 logger =====")

    @perf
    def task_default(n):
        time.sleep(random.uniform(0.01, 0.03))
        return n * 2

    for i in range(3):
        task_default(i)

    print("\n===== 测试 2: 使用外部 logger =====")
    os.makedirs("./logs", exist_ok=True)
    external_logger = EasyLogManager.get_logger(
        name="external_perf",
        log_file="external_perf.log",
        log_folder="./logs",
        level="DEBUG",
    )

    @perf(log_obj=external_logger, color="green")
    def task_external(n):
        time.sleep(random.uniform(0.01, 0.03))
        return n + 10

    for i in range(3):
        task_external(i)

    print("\n===== 测试 3: 通过 new_perf 配置一次性装饰器 =====")
    new_perf = perf(log_file="auto_perf.log", log_folder="./auto_logs", color="magenta")

    @new_perf
    def task_new1(n):
        time.sleep(random.uniform(0.01, 0.03))
        return n + 1

    @new_perf
    def task_new2(n):
        time.sleep(random.uniform(0.01, 0.03))
        return n + 2

    for i in range(3):
        task_new1(i)
        task_new2(i)

    # 打印统计汇总
    print("\n===== 统计结果汇总 =====")
    for name, stat in get_perf_stats().items():
        print(
            f"[SUMMARY] {name} | 调用 {stat.count} 次 | "
            f"平均: {stat.avg_time:.6f}s | 最大: {stat.max_time:.6f}s | "
            f"总耗时: {stat.total_time:.6f}s"
        )
