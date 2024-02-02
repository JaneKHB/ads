import time

import redis

from config.app_config import D_SUCCESS, D_ERROR, D_PROC_START


def get_redis_process_status(pname, sname, pno=None):
    # time.sleep(1)
    # # todo
    # return D_SUCCESS, D_PROC_START

    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    if pno is not None:
        key = f"{pname}:{sname}:{str(pno)}"
    else:
        key = f"{pname}:{sname}"

    value = r.get(key)
    if value:
        val = int(value.decode('utf-8'))    # byte -> str -> int
        return D_SUCCESS, val
    else:
        return D_ERROR, None


def set_redis_process_status(pname, sname, pno=None, val=None):
    if pno is not None:
        key = f"{pname}:{sname}:{str(pno)}"
    else:
        key = f"{pname}:{sname}"

    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    r.setex(key, 3600, str(val))
    return D_SUCCESS


def get_redis_global_status(key: str):
    # if shutdown return 1
    return 0
