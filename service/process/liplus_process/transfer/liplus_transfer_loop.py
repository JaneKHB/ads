"""
=========================================================================================
 :mod:`proc_fdt_deploy` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import sys
import time
import signal

import service.logger.logger_service as log
import config.app_config as config

from typing import Union
from service.process.liplus_process.transfer.file_transfer import LiplusFileTransfer

exit_flag = False   # subprocess Exit Flag
loop_interval = 5   # second

def SignalHandler(signum, frame):
    signal_name_map = {getattr(signal, name): name for name in dir(signal) if name.startswith('SIG')}
    signal_name = signal_name_map.get(signum, f'Unknown signal ({signum})')

    global exit_flag
    exit_flag = True


def liplus_transfer_loop(logger, pname, sname, pno: Union[int, None]):
    while True:
        # check Exit Flag
        if exit_flag:
            break

        # Liplus_batch FileTransfer.bat
        obj = LiplusFileTransfer(logger, pname, sname, pno)
        obj.start()

        # time.sleep(loop_interval)
        break


if __name__ == '__main__':
    argv = sys.argv
    script_path = argv[0]
    pno = int(argv[1])

    # signal handler(sigint, sigterm)
    signal.signal(signal.SIGINT, SignalHandler)
    signal.signal(signal.SIGTERM, SignalHandler)

    logger_path = config.FILE_LOG_LIPLUS_TRANSFER_PATH.format(f"_{pno}")
    logger = log.FileLogger(config.LOG_NAME_LIPLUS_TRANSFER, log.Setting(logger_path))

    liplus_transfer_loop(logger, "LIPLUS", "TRANSFER", pno)