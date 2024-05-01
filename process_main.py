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
from typing import Union
import service.logger.logger_service as log

from config.app_config import config_ini, FILE_LOG_MAIN_PATH, FILE_LOG_LIPLUS_GET_PATH, FILE_LOG_LIPLUS_TRANSFER_PATH, \
    FILE_LOG_LIPLUS_DOWNLOAD_PATH, FILE_LOG_LIPLUS_UPLOAD_PATH, FILE_LOG_LIPLUS_PATH, LIPLUS_ONDEMAND_DIR, \
    CHECK_CAPA_CURRENT_DIR, FILE_LOG_PATH
from service.ini.ini_service import get_ini_value

exit_flag = False  # mainprocess Exit Flag
subprocess_arr = []


# logger = log.Logger("MAIN", log.Setting(config_ini.FILE_LOG_MAIN_PATH))


def SignalHandler(signum, frame):
    signal_name_map = {getattr(signal, name): name for name in dir(signal) if name.startswith('SIG')}
    signal_name = signal_name_map.get(signum, f'Unknown signal ({signum})')

    print(f"[main] 시그널 {signal_name} 을 수신했습니다.")

    if str(signal_name) == "SIGINT" or str(signal_name) == "SIGTERM" or signum == 2 or signum == 15:
        global exit_flag
        exit_flag = True


def RunSubProcess(script_path, enable_value, pno: Union[int, None]=None):
    if enable_value == "1":
        if pno is None:
            process = subprocess.Popen(["python", script_path], stdin=None, stdout=None, stderr=None, close_fds=True)
            subprocess_arr.append(process)
        else:
            for i in range(1, int(pno) + 1):
                process = subprocess.Popen(["python", script_path, str(i)], stdin=None, stdout=None, stderr=None, close_fds=True)
                subprocess_arr.append(process)


def CheckExitFlag():
    while True:
        if exit_flag:
            WaitSubProcess()
            break  # Exit Main Process

        time.sleep(1)


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


def makedir(liplus_get_cnt, liplus_transfer_cnt):
    make_logger_folder(liplus_get_cnt, liplus_transfer_cnt)

    # Make ondemand xml directory
    os.makedirs(os.path.dirname(LIPLUS_ONDEMAND_DIR), exist_ok=True)

    pass


def make_logger_folder(liplus_get_cnt, liplus_transfer_cnt):
    # fdt devlog
    # ....

    os.makedirs(os.path.dirname(FILE_LOG_PATH), exist_ok=True)          # devlog default
    os.makedirs(os.path.dirname(FILE_LOG_LIPLUS_PATH), exist_ok=True)   # devlog liplus
    os.makedirs(os.path.dirname(CHECK_CAPA_CURRENT_DIR), exist_ok=True) # capa check

    print("make logger folder success")


if __name__ == '__main__':
    # signal handler(sigint, sigterm)
    signal.signal(signal.SIGINT, SignalHandler)
    signal.signal(signal.SIGTERM, SignalHandler)

    liplus_get_cnt = get_ini_value(config_ini, "LIPLUS", "LIPLUS_GET_CNT")
    liplus_transfer_cnt = get_ini_value(config_ini, "LIPLUS", "LIPLUS_TRANSFER_CNT")

    # 폴더 생성
    makedir(liplus_get_cnt, liplus_transfer_cnt)

    # run subprocess
    # khb FIXME. 서브프로세스로 "python xx.py" 를 실행시킬 시, ModuleNotFoundError 에러 발생. 해결방안 검토 중
    # 검토 방안(1안으로 진행)
    # 1. 서브 프로세스로 ['python', './service/...../liplus_get_loop.py 1' 실행(기존방식) + PYTHONPATH 환경변수 세팅("/ADS/appsrc")
    # 2. 서브 프로세스로 ['python', '-m', 'service.process.liplus_process.get.liplus_get_loop 1'] 실행(-m 옵션: 모듈을 스크립트로 실행)
    # RunSubProcess("./service/process/proc_fdt_download.py", get_ini_value(config_ini, "GLOBAL", "EEC_DOWNLOAD_ENABLE"))
    # RunSubProcess("./service/process/proc_fdt_deploy.py", get_ini_value(config_ini, "GLOBAL", "EEC_DEPLOY_ENABLE"))
    # RunSubProcess("./service/process/proc_fdt_upload.py", get_ini_value(config_ini, "GLOBAL", "EEC_UPLOAD_ENABLE"))
    RunSubProcess("./service/process/liplus_process/get/liplus_get_loop.py", get_ini_value(config_ini, "GLOBAL", "LIPLUS_GET_ENABLE"), liplus_get_cnt)
    RunSubProcess("./service/process/liplus_process/transfer/liplus_transfer_loop.py", get_ini_value(config_ini, "GLOBAL", "LIPLUS_TRANSFER_ENABLE"), liplus_transfer_cnt)
    RunSubProcess("./service/process/liplus_process/download/liplus_download_loop.py", get_ini_value(config_ini, "GLOBAL", "LIPLUS_ONDEMANDCOLLECTDOWNLOAD_ENABLE"))
    RunSubProcess("./service/process/liplus_process/upload/liplus_upload_loop.py", get_ini_value(config_ini, "GLOBAL", "LIPLUS_COLLECTREQUESTFILEUPLOAD_ENABLE"))

    # check exit flag
    CheckExitFlag()
