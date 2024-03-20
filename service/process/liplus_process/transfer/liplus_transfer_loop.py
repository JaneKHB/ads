"""
=========================================================================================
 :mod:`proc_fdt_deploy` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import time
import signal
from typing import Union
from service.logger.db_logger_service import DbLogger
from service.process.liplus_process.transfer.file_transfer import LiplusFileTransfer


exit_flag = False   # subprocess Exit Flag
loop_interval = 5   # second


def SignalHandler(signum, frame):
    signal_name_map = {getattr(signal, name): name for name in dir(signal) if name.startswith('SIG')}
    signal_name = signal_name_map.get(signum, f'Unknown signal ({signum})')

    global exit_flag
    exit_flag = True


def liplus_transfer_loop(pname, sname, pno: Union[int, None]):
    logger = DbLogger(pname, sname, pno)
    while True:
        # check Exit Flag
        if exit_flag:
            break

        # Liplus_batch FileTransfer.bat
        obj = LiplusFileTransfer(logger, pname, sname, pno)
        obj.start()

        time.sleep(loop_interval)


if __name__ == '__main__':
    # signal handler(sigint, sigterm)
    signal.signal(signal.SIGINT, SignalHandler)
    signal.signal(signal.SIGTERM, SignalHandler)

    liplus_transfer_loop("LIPLUS", "TRANSFER", 1)