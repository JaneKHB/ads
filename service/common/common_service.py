import os
import shutil

from config.app_config import D_ERROR, D_SUCCESS


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
                    shutil.copy2(source_file_path, destination_file_path)
            logger.info(f"Files from '{source_folder}' copied to '{destination_folder}' successfully.")
        except FileNotFoundError:
            logger.warn(f"Folder  not found.")
            return D_ERROR
        except Exception as e:
            logger.warn(f"Error copying files: {e}")
            return D_ERROR
    return D_SUCCESS


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
            return D_ERROR
        except Exception as e:
            logger.warn(f"Error deleting folder: {e}")
            return D_ERROR
    return D_SUCCESS
