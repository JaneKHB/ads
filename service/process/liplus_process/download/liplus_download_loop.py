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

import common.loggers.common_logger as log
import config.app_config as config

from typing import Union
from service.process.liplus_process.download.collect_file_download import CollectFileDownload

from service.ini.ini_service import get_ini_value

exit_flag = False   # subprocess Exit Flag
loop_interval = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_DOWNLOAD_CYCLE_TIME"))   # second
logger = log.TimedLogger(config.PROC_NAME_LIPLUS_DOWN, log.Setting(config.FILE_LOG_LIPLUS_DOWNLOAD_PATH))


def signal_handler(signum, frame):
    signal_name_map = {getattr(signal, name): name for name in dir(signal) if name.startswith('SIG')}
    signal_name = signal_name_map.get(signum, f'Unknown signal ({signum})')

    global exit_flag
    exit_flag = True


# \ADS\OnDemandCollectDownload\LoopScript\Download_Loop.bat
def liplus_download_loop(pname, sname, pno: Union[int, None], is_test=False):
    while True:
        # check Exit Flag
        if exit_flag:
            break

        # \ADS\OnDemandCollectDownload\collectFileDownload.bat
        obj = CollectFileDownload(logger, pname, sname, pno)
        obj.start(logger)

        if is_test:
            break
        else:
            time.sleep(loop_interval)

if __name__ == '__main__':
    # signal handler(sigint, sigterm)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # for test. loop runs only once
    is_test = False

    # LIPLUS_COLLECTREQUESTFILEUPLOAD(LIPLUS_DOWN)
    proc_name = config.PROC_NAME_LIPLUS_DOWN.split('_')
    liplus_download_loop(proc_name[0], proc_name[1], None, is_test)
