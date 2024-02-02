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

from config.app_config import D_SHUTDOWN, D_PROC_START, D_PROC_ING, D_PROC_END, config_ini, D_SUCCESS, D_REDIS_SHUTDOWN_KEY
from service.ini.ini_service import get_ini_value
from service.logger.db_logger_service import DbLogger
from service.process.fdt_process.file_download import FdtFileDownload
from service.process.fdt_process.fpa_trace import FdtFpaTrace
from service.process.fdt_process.move_to_ads2 import FdtMoveToAds2
from service.redis.redis_service import get_redis_process_status, get_redis_global_status, set_redis_process_status


def fdt_download_loop(pname, sname, pno: Union[int, None]):
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

        # fdt_batch FileDownload.bat
        obj = FdtFileDownload(logger, pname, sname, pno)
        obj.start()

        # fdt_batch MoveToADS2.bat
        obj = FdtMoveToAds2(logger, pname, sname, pno)
        obj.start()

        # fdt_batch FPATrace.bat
        fpa_trace_enable = get_ini_value(config_ini, "EEC", "EEC_FPA_TRACE_ENABLE")
        if fpa_trace_enable == "1":
            obj = FdtFpaTrace(logger, pname, sname, pno)
            obj.start()

        # Process進行完了を通知
        set_redis_process_status(pname, sname, pno, D_PROC_END)


if __name__ == '__main__':
    fdt_download_loop("FDT", "DOWNLOAD", None)
