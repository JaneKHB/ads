"""
=========================================================================================
 :mod:`proc_liplus_upload` --- 。
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
from service.process.liplus_process.upload.collect_file_upload import CollectFileUpload

from service.ini.ini_service import get_ini_value

exit_flag = False   # subprocess Exit Flag
loop_interval = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_UPLOAD_CYCLE_TIME"))   # second
logger = log.TimedLogger(config.PROC_NAME_LIPLUS_UPLOAD, log.Setting(config.FILE_LOG_LIPLUS_UPLOAD_PATH))


def signal_handler(signum, frame):
    signal_name_map = {getattr(signal, name): name for name in dir(signal) if name.startswith('SIG')}
    signal_name = signal_name_map.get(signum, f'Unknown signal ({signum})')

    global exit_flag
    exit_flag = True


# \ADS\CollectRequestFileUpload\LoopScript\Upload_Loop.bat
def liplus_upload_loop(pname, sname, pno: Union[int, None], is_test=False):
    while True:
        # check Exit Flag
        if exit_flag:
            break

        # \ADS\CollectRequestFileUpload\Auto_Upload.bat
        obj = CollectFileUpload(logger, pname, sname, pno)
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

    # LIPLUS_ONDEMANDCOLLECTDOWNLOAD(LIPLUS_UPLOAD)
    proc_name = config.PROC_NAME_LIPLUS_UPLOAD.split('_')
    liplus_upload_loop(proc_name[0], proc_name[1], None, is_test)
