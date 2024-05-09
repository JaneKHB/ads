import time
from logging import Logger
from functools import wraps

# 함수 __name__ 변경
def rename(newname):
    def wrapper(f):
        f.__name__ = newname
        return f
    return wrapper

# 함수 파라미터에 Logger있어야 로그 찍힘.
def check_process_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = None
        for i in range(len(args)):
            if type(args[i]) is Logger:
                logger = args[i]
                break

        if logger is not None:
            logger.info(f"Start [{func.__name__}]")

        proc_start_time = time.time()
        res = func(*args, **kwargs)
        processing_time = time.time() - proc_start_time

        if logger is not None:
            logger.info(f"Total time for the [{func.__name__}] : {processing_time :.3f}[sec]")
        return res
    return wrapper