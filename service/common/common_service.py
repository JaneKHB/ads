import os
import shutil
import stat

import pandas as pd
import config.app_config as config
import common.loggers.common_logger as log

from pathlib import Path
from service.ini.ini_service import get_ini_value
from sys import platform


def check_unknown(fname):
    """
    REM ファイルが最後かどうか確認する。Unknownが返ってきた場合はもう取るファイルは無い。

    :param fname:
    :return:
    """
    if os.path.exists(fname):
        try:
            with open(fname, 'r', encoding="utf-8") as input_file:
                for line in input_file:
                    if "Unknown" in line:
                        return 1
        except Exception as e:
            return 0
    return 0


def on_rm_error(func, path, exc_info):
    # path contains the path of the file that couldn't be removed
    # let's just assume that it's read-only and unlink it.
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)


def rmtree(path):
    shutil.rmtree(path, onerror=on_rm_error)


def remove_files_in_folder(folder):
    list_dir = os.listdir(folder)
    for filename in list_dir:
        file = folder + os.sep + filename
        if os.path.exists(file) and os.path.isfile(file):
            os.remove(file)


def xcopy_file_to_dir(logger, source_folder, destination_folder):
    # call :execute xcopy %ADS2_FOLDER%\%TOOLID%_moved\* %REG_FOLDER%\ /R /Y
    if os.path.exists(source_folder) and os.path.exists(destination_folder):
        try:
            for root, dirs, files in os.walk(source_folder):
                for file in files:
                    source_file_path = os.path.join(root, file)
                    destination_file_path = os.path.join(destination_folder, file)
                    if not os.path.exists(destination_file_path):
                        shutil.copy2(source_file_path, destination_file_path)
            logger.info(f"Files from '{source_folder}' copied to '{destination_folder}' successfully.")
        except FileNotFoundError:
            logger.warn(f"Folder  not found.")
            return config.D_ERROR
        except Exception as e:
            logger.warn(f"Error copying files: {e}")
            return config.D_ERROR
    return config.D_SUCCESS


def rmdir_func(logger, dir_path):
    # call :execute rmdir /S /Q %ADS2_FOLDER%\%TOOLID%_moved
    if os.path.exists(dir_path):
        try:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    source_file_path = os.path.join(root, file)
                    os.remove(source_file_path)

            shutil.rmtree(dir_path)
        except FileNotFoundError:
            logger.warn(f"Folder not found.")
            return config.D_ERROR
        except Exception as e:
            logger.warn(f"Error deleting folder: {e}")
            return config.D_ERROR
    return config.D_SUCCESS

def file_size_logging(logger, type, file_path, tool_id =""):

    # 로그경로, 파일 사이즈 초기화
    size_mb = None
    log_path = Path(config.FILE_LOG_LIPLUS_FILE_TRANSFER_PATH)
    file = Path(file_path)
    if file.exists():
        size_mb = file.stat().st_size / (1024 * 1024)

    # 로그 메세지, 헤더 초기화
    log_msg = f"{type},{tool_id},{file_path},{size_mb}"
    header = "time,subprocess_name,up/down,tool_id,filename,filesize(MB)\n"

    file_size_logger = log.TimedLogger(logger.name, log.Setting(log_path.absolute(), True))

    with open(log_path.absolute()) as f:
        first_line = f.readline()

    # 첫 줄이 헤더랑 다를 경우 첫줄에 헤더 넣기
    if header != first_line:
        file_size_logger.handlers.clear()
        with open(log_path.absolute(), "r+") as f:
            content = f.read()
            f.truncate(0)
            f.seek(0)
            f.write(header)
            f.write(content)
        file_size_logger = log.TimedLogger(logger.name, log.Setting(log_path.absolute(), True))

    # 로그
    file_size_logger.info(log_msg)

    # 핸들러 초기화 함으로서 중복 기록 방지
    file_size_logger.handlers.clear()

def create_ulfile_tmp(file_path, boundary):
    file = Path(file_path)
    file_tmp = Path(f"{file.absolute()}.tmp")

    if file_tmp.exists():
        file_tmp.unlink(missing_ok=True)

    # khb. fixme. "\n" 만 사용해서 만들어지는 tmp 파일은 리눅스에서는 wget post 명령어 사용 시에 에러 발생
    # khb. fixme. os 에 따른 crlf 처리 필요(windows: \n, linux : \r\n)
    crlf = "\n"
    if "linux" in platform:
        crlf = "\r\n"

    content_head = f'--{boundary}{crlf}' \
                   f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(file)}"{crlf}' \
                   f'Content-Type: multipart/form-data{crlf}' \
                   f'{crlf}'
    content_tail = f'{crlf}' \
                   f'--{boundary}--{crlf}'
    with open(file_tmp.absolute(), "w") as f, open(file_path.absolute(), 'r') as f_tmp:
        f.write(content_head)
        f.write(f_tmp.read())
        f.write(content_tail)

    return file_tmp


def get_csv_info(module, type, pno=0):
    file_path = None
    ini_section = None
    ini_key = None
    read_names = None
    read_dttype = None

    if module == "LIPLUS":
        if type == "UPLOAD":
            file_path = config.LIPLUS_UPLOAD_INFO_CSV_PATH
            ini_section = module
            ini_key = "LIPLUS_UPLOAD_INFO_SKIP_LINE"
            read_names = config.LIPLUS_UPLOAD_INFO_HEADER
            read_dttype = config.LIPLUS_UPLOAD_DATA_TYPE
        elif type == "DOWNLOAD":
            file_path = config.LIPLUS_DOWNLOAD_INFO_CSV_PATH
            ini_section = module
            ini_key = "LIPLUS_DOWNLOAD_INFO_SKIP_LINE"
            read_names = config.LIPLUS_DOWNLOAD_INFO_HEADER
            read_dttype = config.LIPLUS_DOWNLOAD_DATA_TYPE
        elif type == "GET" or type == "TRANSFER":
            file_path = config.LIPLUS_TOOL_CSV_PATH.format(pno)
            ini_section = module
            ini_key = "LIPLUS_TOOL_INFO_SKIP_LINE"
            read_names = config.LIPLUS_TOOL_INFO_HEADER
            read_dttype = config.LIPLUS_TOOL_DATA_TYPE
    elif module == "FDT":
        if type == "UPLOAD":
            file_path = config.FDT_UPTOOL_CSV_PATH
            ini_section = "EEC"
            ini_key = "EEC_UPTOOL_INFO_SKIP_LINE"
            read_names = config.FDT_UPTOOL_INFO_HEADER
            read_dttype = config.FDT_UPTOOL_DATA_TYPE
        elif type == "DOWNLOAD":
            file_path = config.FDT_TOOL_CSV_PATH
            ini_section = "EEC"
            ini_key = "EEC_TOOL_INFO_SKIP_LINE"
            read_names = config.FDT_TOOL_INFO_HEADER
            read_dttype = config.FDT_TOOL_DATA_TYPE

    verification_csv()

    skiprows = int(get_ini_value(config.config_ini, ini_section, ini_key))
    tool_df = pd.read_csv(file_path, names=read_names, dtype=read_dttype,
                          encoding='shift_jis',
                          skiprows=skiprows, sep=',', index_col=False)
    return tool_df

def verification_csv():
    # shlee todo verification_csv
    pass
