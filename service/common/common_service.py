import datetime
import os
import shutil
import stat

import pandas as pd
import config.app_config as config
import util.time_util as time_util

from pathlib import Path
from service.ini.ini_service import get_ini_value

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

def on_rm_error( func, path, exc_info):
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

def file_size_logging(type, file_path, log_path):

    log = Path(log_path)
    if not log.exists():
        with open(log, "w") as f:
            f.write("up/down,filename,filesize(MB)\n")

    file = Path(file_path)
    if file.exists():
        size_mb = file.stat().st_size / (1024 * 1024)
        with open(log, "a") as f:
            f.write(f"{type},{file.absolute()},{size_mb}\n")

def create_upfile_tmp(file_path, boundary):
    file = Path(file_path)
    file_tmp = Path(file.absolute() + ".tmp")

    if file_tmp.exists():
        file_tmp.unlink(missing_ok=True)

    content_head = f'--{boundary}\n' \
                   f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(file)}"\n' \
                   f'Content-Type: multipart/form-data\n' \
                   f'.\n'
    content_tail = f'\n.\n' \
                   f'--{boundary}--\n'
    with open(file_tmp.absolute(), "w") as f, open(file_path.absolute(), 'r') as f_tmp:
        f.write(content_head)
        f.write(f_tmp.read())
        f.write(content_tail)

    return file_tmp

def check_capacity(bat_name):
    stat = shutil.disk_usage(config.CHECK_CAPA_DRIVE)
    current_per = stat.free / stat.total * 100
    log_path = os.path.join(config.CHECK_CAPA_CURRENT_DIR, "logs", "Disk_Limit.log")

    if current_per < config.CHECK_CAPA_LIMIT_PERCENT:
        input_data = f"{bat_name}\n" \
                     f"{datetime.datetime.now().strftime(time_util.TIME_FORMAT_1)[:-4]}" \
                     f"{config.CHECK_CAPA_DRIVE} の空き容量は {current_per} ％です\n" \
                     f"空き容量がリミットを下回ったので処理を終了します\n"

        with open(log_path, "a") as f:
            f.write(input_data)
        return False

    return True

def get_csv_info(module, type):
    file_path = None
    ini_section = None
    ini_key = None
    read_names = None
    read_dttype = None

    if module == "LIPLUS":
        if type == "UPLOAD":
            file_path = config.LIPLUS_UPLOAD_INFO_CSV
            ini_section = module
            ini_key = "LIPLUS_UPLOAD_INFO_SKIP_LINE"
            read_names = config.LIPLUS_UPLOAD_INFO_HEADER
            read_dttype = config.LIPLUS_UPLOAD_DATA_TYPE
        elif type == "DOWNLOAD":
            file_path = config.LIPLUS_DOWNLOAD_INFO_CSV
            ini_section = module
            ini_key = "LIPLUS_DOWNLOAD_INFO_SKIP_LINE"
            read_names = config.LIPLUS_DOWNLOAD_INFO_HEADER
            read_dttype = config.LIPLUS_DOWNLOAD_DATA_TYPE
    elif module == "FDT":
        pass

    skiprows = int(get_ini_value(config.config_ini, ini_section, ini_key))
    tool_df = pd.read_csv(file_path, names=read_names, dtype=read_dttype,
                          encoding='shift_jis',
                          skiprows=skiprows, sep=',', index_col=False)
    return tool_df
