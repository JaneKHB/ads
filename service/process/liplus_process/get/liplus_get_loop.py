"""
=========================================================================================
 :mod:`proc_fdt_download` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import sys
import time
import signal

import common.loggers.common_logger as log
import config.app_config as config

from typing import Union
from service.process.liplus_process.get.file_get import LiplusFileGet

from service.ini.ini_service import get_ini_value

exit_flag = False  # subprocess Exit Flag
loop_interval = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_GET_CYCLE_TIME"))  # second

def signal_handler(signum, frame):
    signal_name_map = {getattr(signal, name): name for name in dir(signal) if name.startswith('SIG')}
    signal_name = signal_name_map.get(signum, f'Unknown signal ({signum})')

    global exit_flag
    exit_flag = True


def liplus_get_loop(logger, pname, sname, pno: Union[int, None], is_test=False):
    while True:
        # check Exit Flag
        if exit_flag:
            break

        # Liplus_batch FileGet.bat
        obj = LiplusFileGet(logger, pname, sname, pno)
        obj.start(logger)

        if is_test:
            break
        else:
            time.sleep(loop_interval)


if __name__ == '__main__':
    argv = sys.argv
    script_path = argv[0]
    pno = int(argv[1])

    # signal handler(sigint, sigterm)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger_path = config.FILE_LOG_LIPLUS_GET_PATH.format(f"_{pno}")
    logger = log.TimedLogger(config.PROC_NAME_LIPLUS_GET, log.Setting(logger_path))

    # for test. loop runs only once
    is_test = False

    # LIPLUS_GET
    proc_name = config.PROC_NAME_LIPLUS_GET.split('_')
    liplus_get_loop(logger, proc_name[0], proc_name[1], pno, is_test)
