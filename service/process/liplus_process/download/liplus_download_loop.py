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

import service.logger.logger_service as log
import config.app_config as config

from typing import Union

from service.logger.db_logger_service import DbLogger
from service.process.liplus_process.download.collect_file_download import CollectFileDownload

exit_flag = False   # subprocess Exit Flag
loop_interval = 5   # second
logger = log.FileLogger("LIPLUS_DOWN", log.Setting(config.FILE_LOG_LIPLUS_DOWNLOAD_PATH))

def SignalHandler(signum, frame):
    signal_name_map = {getattr(signal, name): name for name in dir(signal) if name.startswith('SIG')}
    signal_name = signal_name_map.get(signum, f'Unknown signal ({signum})')

    global exit_flag
    exit_flag = True


# \ADS\OnDemandCollectDownload\LoopScript\Download_Loop.bat
def liplus_download_loop(pname, sname, pno: Union[int, None]):
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