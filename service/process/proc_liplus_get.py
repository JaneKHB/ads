"""
=========================================================================================
 :mod:`proc_fdt_download` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import time
from typing import Union

from config.app_config import D_SHUTDOWN, D_PROC_START, D_PROC_ING, D_PROC_END, D_SUCCESS, D_REDIS_SHUTDOWN_KEY
from service.logger.db_logger_service import DbLogger
from service.process.liplus_process.file_get import LiplusFileGet
from service.redis.redis_service import get_redis_process_status, get_redis_global_status, set_redis_process_status


def liplus_get_loop(pname, sname, pno: Union[int, None]):
    logger = DbLogger(pname, sname, pno)
    while True:
        # Mainが緊急終了状態
        if get_redis_global_status(D_REDIS_SHUTDOWN_KEY) == D_SHUTDOWN:
            break

        # 1Cycleを開始してもいいか確認。
        rtn, val = get_redis_process_status(pname, sname, pno)
        if rtn != D_SUCCESS or val != D_PROC_START:
            time.sleep(1)
            continue

        # Process進行中に設定
        set_redis_process_status(pname, sname, pno, D_PROC_ING)

        # Liplus_batch FileGet.bat
        obj = LiplusFileGet(logger, pname, sname, pno)
        obj.start()

        # Process進行完了を通知
        set_redis_process_status(pname, sname, pno, D_PROC_END)


if __name__ == '__main__':
    liplus_get_loop("LIPLUS", "GET", 1)
