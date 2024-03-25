"""
=========================================================================================
 :mod:`process_main` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import os
import subprocess
import time
import signal

import service.logger.logger_service as log

from config.app_config import config_ini, FILE_LOG_MAIN_PATH, FILE_LOG_LIPLUS_GET_PATH, FILE_LOG_LIPLUS_TRANSFER_PATH, \
    FILE_LOG_LIPLUS_DOWNLOAD_PATH, FILE_LOG_LIPLUS_UPLOAD_PATH
from service.ini.ini_service import get_ini_value

exit_flag = False  # mainprocess Exit Flag
subprocess_arr = []
logger = log.Logger("MAIN", log.Setting(config_ini.FILE_LOG_MAIN_PATH))


def SignalHandler(signum, frame):
    signal_name_map = {getattr(signal, name): name for name in dir(signal) if name.startswith('SIG')}
    signal_name = signal_name_map.get(signum, f'Unknown signal ({signum})')

    print(f"[main] 시그널 {signal_name} 을 수신했습니다.")

    if str(signal_name) == "SIGINT" or str(signal_name) == "SIGTERM":
        global exit_flag
        exit_flag = True


def RunSubProcess(script_path, enable_value):
    if enable_value == 1:
        process = subprocess.Popen(["python", script_path], stdin=None, stdout=None, stderr=None, close_fds=True)
        subprocess_arr.append(process)


def CheckExitFlag():
    while True:
        if exit_flag:
            WaitSubProcess()
            break  # Exit Main Process

        time.sleep(10)


def WaitSubProcess():
    while True:
        is_subprocess_exit = True

        for process in subprocess_arr:
            # check if exist alive subprocess
            if process.poll() is None:  # If the process is alive, return none
                is_subprocess_exit = False

        if is_subprocess_exit:
            break

        time.sleep(3)


def makedir():
    # Make log directory
    os.makedirs(os.path.dirname(FILE_LOG_MAIN_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(FILE_LOG_LIPLUS_GET_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(FILE_LOG_LIPLUS_TRANSFER_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(FILE_LOG_LIPLUS_DOWNLOAD_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(FILE_LOG_LIPLUS_UPLOAD_PATH), exist_ok=True)

    pass

if __name__ == '__main__':

    # 폴더 생성
    makedir()

    # signal handler(sigint, sigterm)
    signal.signal(signal.SIGINT, SignalHandler)
    signal.signal(signal.SIGTERM, SignalHandler)

    # run subprocess
    RunSubProcess("./service/process/proc_fdt_download.py", get_ini_value(config_ini, "GLOBAL", "EEC_DOWNLOAD_ENABLE"))
    RunSubProcess("./service/process/proc_fdt_deploy.py", get_ini_value(config_ini, "GLOBAL", "EEC_DEPLOY_ENABLE"))
    RunSubProcess("./service/process/proc_fdt_upload.py", get_ini_value(config_ini, "GLOBAL", "EEC_UPLOAD_ENABLE"))
    RunSubProcess("./service/process/liplus_process/get/liplus_get_loop.py", get_ini_value(config_ini, "GLOBAL", "LIPLUS_GET_ENABLE"))
    RunSubProcess("./service/process/liplus_process/transfer/liplus_transfer_loop.py", get_ini_value(config_ini, "GLOBAL", "LIPLUS_TRANSFER_ENABLE"))
    RunSubProcess("./service/process/liplus_process/download/liplus_download_loop.py", get_ini_value(config_ini, "GLOBAL", "LIPLUS_ONDEMANDCOLLECTDOWNLOAD_ENABLE"))
    RunSubProcess("./service/process/liplus_process/upload/liplus_upload_loop.py", get_ini_value(config_ini, "GLOBAL", "LIPLUS_COLLECTREQUESTFILEUPLOAD_ENABLE"))

    # check exit flag
    CheckExitFlag()

