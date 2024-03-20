"""
=========================================================================================
 :mod:`proc_liplus_download` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------

import time
import signal
from typing import Union

from config.app_config import D_SHUTDOWN, D_PROC_START, D_PROC_ING, D_PROC_END, D_SUCCESS, D_REDIS_SHUTDOWN_KEY
from service.logger.db_logger_service import DbLogger
from service.process.liplus_process.download.collect_file_download import CollectFileDownload
from service.redis.redis_service import get_redis_process_status, get_redis_global_status, set_redis_process_status


exit_flag = False   # subprocess Exit Flag
loop_interval = 5   # second


def SignalHandler(signum, frame):
    signal_name_map = {getattr(signal, name): name for name in dir(signal) if name.startswith('SIG')}
    signal_name = signal_name_map.get(signum, f'Unknown signal ({signum})')

    global exit_flag
    exit_flag = True


# \ADS\OnDemandCollectDownload\LoopScript\Download_Loop.bat
def liplus_download_loop(pname, sname, pno: Union[int, None]):
    logger = DbLogger(pname, sname, pno)
    while True:
        # check Exit Flag
        if exit_flag:
            break

        # \ADS\OnDemandCollectDownload\collectFileDownload.bat
        obj = CollectFileDownload(logger, pname, sname, pno)
        obj.start()

        time.sleep(loop_interval)

if __name__ == '__main__':
    # signal handler(sigint, sigterm)
    signal.signal(signal.SIGINT, SignalHandler)
    signal.signal(signal.SIGTERM, SignalHandler)

    liplus_download_loop("LIPLUS", "DOWNLOAD", None)