"""
=========================================================================================
 :mod:`proc_fdt_download` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import time
import signal

from typing import Union

import service.logger.logger_service as log
import config.app_config as config

from config.app_config import D_SHUTDOWN, D_PROC_START, D_PROC_ING, D_PROC_END, config_ini, D_SUCCESS, D_REDIS_SHUTDOWN_KEY
from service.ini.ini_service import get_ini_value
from service.process.fdt_process.download.file_download import FdtFileDownload
from service.process.fdt_process.download.fpa_trace import FdtFpaTrace
from service.process.fdt_process.download.move_to_ads2 import FdtMoveToAds2


exit_flag = False   # subprocess Exit Flag
loop_interval = 30   # second
logger = log.FileLogger(config.LOG_NAME_FDT_DOWN, log.Setting(config.FILE_LOG_LIPLUS_DOWNLOAD_PATH))

def SignalHandler(signum, frame):
    signal_name_map = {getattr(signal, name): name for name in dir(signal) if name.startswith('SIG')}
    signal_name = signal_name_map.get(signum, f'Unknown signal ({signum})')

    global exit_flag
    exit_flag = True

# \ADS\LoopScript\Download_Loop.bat
def fdt_download_loop(pname, sname, pno: Union[int, None]):
    while True:
        # check Exit Flag
        if exit_flag:
            break

        # \ADS\fdt_batch\FileDownload.bat
        obj = FdtFileDownload(logger, pname, sname, pno)
        obj.start()

        # \ADS\fdt_batch\MoveToADS2.bat
        obj = FdtMoveToAds2(logger, pname, sname, pno)
        obj.start()

        # \ADS\fdt_batch\FPATrace.bat
        fpa_trace_enable = get_ini_value(config_ini, "EEC", "EEC_FPA_TRACE_ENABLE")
        if fpa_trace_enable == "1":
            obj = FdtFpaTrace(logger, pname, sname, pno)
            obj.start()

        time.sleep(loop_interval)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, SignalHandler)
    signal.signal(signal.SIGTERM, SignalHandler)

    fdt_download_loop("FDT", "DOWNLOAD", None)
