"""
=========================================================================================
 :mod:`file_get` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import datetime
import os
import shutil
import time
import pandas as pd
from typing import Union
from pathlib import Path
from sys import platform

# from config.app_config import D_SUCCESS, config_ini, SECURITYINFO_PATH, \
#     LIPLUS_CURRENT_DIR, LIPLUS_REG_FOLDER_DEFAULT, LIPLUS_REG_FOLDER_TMP, FILE_LOG_LIPLUS_GET_PATH, FILE_LOG_PATH
import config.app_config as config
from service.capa.capa_service import check_capacity
from service.common.common_service import check_unknown, rmdir_func, get_csv_info
from service.remote.remote_service import isExistWget
from service.remote.request import esp_download, subprocess_run, request_subprocess
from service.ini.ini_service import get_ini_value
from service.security.security_service import security_info
from service.zip.sevenzip_service import unzip, isExist7zip


class LiplusFileGet:
    def __init__(self, logger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = config.LIPLUS_CURRENT_DIR
        self.tool_df = get_csv_info("LIPLUS", "GET", self.pno)

        self.ca_name = None
        self.toolid = None  # 装置名 (MachineName)
        self.espaddr = None  # 接続先ESPアドレス (ESP Address)
        self.cntlmt = None  # ダウンロード上限数 (Download Limit)
        self.reg_folder = None  # 正規フォルダパス (* Liplus Data Download Folder)
        self.userid = None  # ユーザID (User Id)
        self.userpasswd = None  # ユーザパスワード (User Password)

        self.retry_max = 5  # rem リトライ上限 (Retry Limit)
        self.retry_sleep = 2  # rem リトライ時のスリープ時間 (Retry Sleep Time)

        # REM 2要素認証の利用有無を判別 (two Factor Auth)
        self.securityinfo_path = config.SECURITYINFO_PATH
        self.securitykey_path = get_ini_value(config.config_ini, "SECURITY", "SECURITYKEY_PATH")
        self.twofactor = {}

        self.logger_header = ""

    def start(self):
        # Capacity Check
        if not check_capacity("LiplusGet"):
            return

        # Processing Start Time
        processing_start_time = time.time()

        for _, elem in self.tool_df.iterrows():
            # 	rem	設定ファイル「LiplusTool.csv」から、
            # 	rem	一行ずつ読み込んで、必要項目を取得する
            # 	rem	--------------------------------------------------------------
            # 	rem	 1:%%i : CollectionPlan名
            # 	rem	 2:%%j : 装置名
            # 	rem	 3:%%k : 接続先ESPアドレス
            # 	rem	 4:%%l : ダウンロード上限数
            # 	rem	 6:%%m : ログインユーザID
            # 	rem	 7:%%n : ログインユーザパスワード
            # 	rem	 8:%%o : ADSサーバー内の保存先パス
            # 	rem	--------------------------------------------------------------
            # 	call %CURRENT_DIR%script\LiplusGet_Tool.bat %%i %%j %%k %%l %%m %%n "%%o" %CURRENT_DIR%

            self._liplus_get_tool(elem.get('ca_name'), elem.get('toolid'), elem.get('espaddr'), elem.get('cntlmt'),
                                 elem.get('userid'), elem.get('userpasswd'), elem.get('reg_folder'))

        # Processing End Time
        processing_end_time = time.time()
        processing_time = processing_end_time - processing_start_time

        # Processing Time logging
        self.logger_header = f"[{self.toolid}]"
        self.logger.info(f"{self.logger_header} Total time for the collection process:{processing_time :.2f}[sec] ")

    # ADS\Liplus_batch\script\LiplusGet_Tool.bat
    def _liplus_get_tool(self, ca_name, toolid, espaddr, cntlmt, userid, userpasswd, reg_folder):
        self.ca_name = ca_name
        self.toolid = toolid  # 装置名 (MachineName)
        self.espaddr = espaddr  # 接続先ESPアドレス (ESP Address)
        self.cntlmt = cntlmt  # ダウンロード上限数 (Download Limit)
        self.userid = userid  # ユーザID (User Id)
        self.userpasswd = userpasswd  # ユーザパスワード (User Password)

        debug_log_path = Path(config.FILE_LOG_PATH, f"{toolid}_debug.log")

        protocol = "http"
        timeout_second = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_ESP_HTTP_TIME_OUT"))
        liplus_get_log_path = os.path.dirname(config.FILE_LOG_LIPLUS_GET_PATH.format(f"_{self.pno}"))

        self.logger_header = f"[{self.toolid}]"
        self.logger.info(f"{self.logger_header} liplus_get_tool start!!")

        # Liplus Data Download Folder
        if reg_folder == "" or pd.isna(reg_folder):
            self.reg_folder = config.LIPLUS_REG_FOLDER_DEFAULT + self.toolid

        # Liplus Data Temp Folder
        reg_folder_tmp = config.LIPLUS_REG_FOLDER_TMP + f"{self.toolid}_Get"

        # Check wget
        if isExistWget(self.logger) != 0:
            return

        # Check 7zip
        if not config.IS_USE_UNZIP_LIB and isExist7zip(self.logger) != 0:
            return

        # Make Liplus Data temp Folder
        if not os.path.exists(reg_folder_tmp):
            self.logger.info(f"{self.logger_header} mkdir reg_folder_tmp '{reg_folder_tmp}'")
            os.makedirs(reg_folder_tmp)

        # Make Liplus Data Download Folder
        if not os.path.exists(self.reg_folder):
            self.logger.info(f"{self.logger_header} mkdir reg_folder '{self.reg_folder}'")
            os.makedirs(self.reg_folder)

        # Check two Factor Auth
        rtn, self.twofactor = security_info(self.logger, self.espaddr, self.securityinfo_path, self.securitykey_path)
        if rtn == config.D_SUCCESS and len(self.twofactor):
            protocol = "https"
            timeout_second = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_ESP_HTTPS_TIME_OUT"))
        elif rtn != config.D_SUCCESS:
            return

        # File Download URL
        url = f"{protocol}://{self.espaddr}/FileServiceCollectionAgent/Download"
        parameter = f"USER={self.userid}&PW={self.userpasswd}&ID=CollectionPlan_{self.ca_name}-01"
        base_url = url + "?" + parameter
        next_url = url + "?" + parameter + "&NEXT=1"

        # test
        # base_url = 'http://10.4.101.69:8080/FileServiceCollectionAgent/Download?USER=inazawa.wataru&PW=CanonCanon&ID=CollectionPlan_C6_AUXCF_PKRF2A1-01'
        # next_url = base_url + "&NEXT=1"

        # Save the download URL as file.
        url_folder_path = liplus_get_log_path + "/" + f"get_url_{self.pno}"
        os.makedirs(url_folder_path, exist_ok=True)

        self._write_to_file(f"{url_folder_path}/{self.toolid}_DL.txt", base_url)
        self._write_to_file(f"{url_folder_path}/{self.toolid}_NXT.txt", next_url)

        # Loop Start
        for i in range(self.cntlmt):
            # Unique File Name
            now = datetime.datetime.now()
            datetimenow = now.strftime("%Y%m%d%H%M%S%f")[:-4]
            fname = f"{reg_folder_tmp}/{self.toolid}-{datetimenow}.zip"

            # Call collection files download url
            download_start_time = time.time()

            if config.IS_USE_WGET:
                # shlee todo twofactor
                command_base = f'wget "{base_url}" -a {debug_log_path.absolute()} -O {fname} -c -t 2 -T 10'
                self.logger.info(f"wget command : {command_base}")
                base_res = request_subprocess(self.logger, command_base, self.retry_max, self.retry_sleep)
            else:
                self.logger.info(f"{self.logger_header} download URL : {base_url}")
                base_res = esp_download(self.logger, base_url, fname, timeout_second, self.twofactor, self.retry_max, self.retry_sleep)

            if debug_log_path.exists():
                with open(debug_log_path.absolute(), "r") as f:
                    read_debug = f.readline()
                self.logger.info(f"{self.logger_header} {read_debug}")
                debug_log_path.unlink(missing_ok=True)

            # If File Download fail after retrying, Loop End
            if base_res == config.D_SUCCESS:
                self.logger.info(f"{self.logger_header} download success. got zip file: {fname}")
            else:
                self.logger.error(f"{self.logger_header} errorcode:2000 msg:Failed to retry collecting {fname} from ESP")
                break

            download_end_time = time.time()
            download_time = download_end_time - download_start_time

            # Check File is Last. If Unknown returns, File is last. There are no more files to take.
            if check_unknown(fname):
                self.logger.info(f"{self.logger_header} findstr \"Unknown\": true. '{fname}'")
                break
            else:
                self.logger.info(f"{self.logger_header} findstr \"Unknown\": false. '{fname}'")

            # Unzip Downloaded File
            unzip_start_time = time.time()
            unzip_cmd = ['7z', 'x', '-aoa', f'-o{reg_folder_tmp}', fname]

            # khb. FIXME. 7zip 명령어(array)를 linux 에서 사용 시, 압축이 풀리지 않는 현상 발생(x 옵션이 아닌 -h 옵션이 적용되는것같음)
            # khb. FIXME. 해당 기능(7zz x -aoa ...) 에 대해서는 Array 가 아닌 String 으로 처리한다.
            if "linux" in platform:
                unzip_cmd[0] = '7zz'
                unzip_cmd = " ".join(unzip_cmd)

            if config.IS_USE_UNZIP_LIB:
                unzip_ret = unzip(self.logger, fname, reg_folder_tmp)
            else:
                unzip_ret = unzip(self.logger, unzip_cmd)

            # if unzip success, 0 returned.
            if unzip_ret != 0:
                self.logger.warn(f"{self.logger_header} The zip file is corrupted.")
                break   # if unzip fail, then loop end

            # Unzipping time
            unzip_end_time = time.time()
            unzip_time = unzip_end_time - unzip_start_time
            self.logger.info(f"{self.logger_header} Unzipping time of a '{fname}':{unzip_time:.3f}[sec]")

            # Logging downloaded files
            size_bytes = os.path.getsize(fname)
            self.logger.info(f"{self.logger_header} file size = {size_bytes} bytes. '{fname}'")

            # Call collection files NEXT url
            self.logger.info(f"{self.logger_header} NXT URL : {next_url}")
            dummy_fname = f"{self.current_dir}dummy_{self.toolid}"

            if config.IS_USE_WGET:
                # shlee todo twofactor
                command_next = f'wget "{next_url}" -a {debug_log_path.absolute()} -O {dummy_fname} -c -t 2 -T 10'
                self.logger.info(f"wget command : {command_next}")
                next_res = request_subprocess(self.logger, command_next, self.retry_max, self.retry_sleep)
            else:
                next_res = esp_download(self.logger, next_url, dummy_fname, timeout_second, self.twofactor, self.retry_max,
                                   self.retry_sleep)

            if debug_log_path.exists():
                with open(debug_log_path.absolute(), "r") as f:
                    read_debug = f.readline()
                self.logger.info(f"{self.logger_header} {read_debug}")
                debug_log_path.unlink(missing_ok=True)

            # If File Next fail after retrying, Logging message.
            if next_res == config.D_SUCCESS:
                self.logger.info(f"{self.logger_header} Next Request command success.")
            else:
                self.logger.error(f"{self.logger_header} errorcode:2001 msg:Failed to retry file deletion instruction to ESP.")

            # Delete Dummy File
            self.logger.info(f"{self.logger_header} dummy file delete start. '{dummy_fname}'")

            dummy_file = Path(dummy_fname)
            self._delete_dummy_file(dummy_file)

            if dummy_file.exists():
                self.logger.error(f"{self.logger_header} errorcode:2003 msg:Failed to retry temporary file '{dummy_file}' deletion.")

            # Move the Liplus data(zip) to REG_FOLDER.
            shutil.move(fname, self.reg_folder)

            # List of files in reg_folder_tmp
            list_dir = os.listdir(reg_folder_tmp)
            self.logger.info(f"{self.logger_header} dir '{reg_folder_tmp}' : {list_dir}")

            # khb. fixme: 폴더를 삭제하는 코드가 ADS_1.2에 새로 추가. ADS_1.2 bat(LiplusGet_Tool.bat)에서도 여러개의 파일을 다운로드 받아야하는데 폴더를 미리 삭제해버리면서 에러 발생!
            # Remove reg_folder_tmp
            # self.logger.info(f"rmdir {reg_folder_tmp}")
            # rmdir_func(self.logger, reg_folder_tmp)

            # Loop End

        # List of files in reg_folder_tmp
        list_dir = os.listdir(reg_folder_tmp)
        self.logger.info(f"{self.logger_header} dir '{reg_folder_tmp}' : {list_dir}")

        # Remove reg_folder_tmp
        self.logger.info(f"{self.logger_header} rmdir '{reg_folder_tmp}'")
        rmdir_func(self.logger, reg_folder_tmp)

        self.logger.info(f"{self.logger_header} LiplusGet_Tool Finished")

    def _req(self):
        pass

    def _write_to_file(self, file_name, content):
        with open(file_name, 'w') as log_file:
            log_file.write(content)

    def _delete_dummy_file(self, dummy_file):
        dummy_file.unlink(missing_ok=True)

        # if dummy file remove fail, retry delete.
        for i in range(1, self.retry_max + 1):
            if not dummy_file.exists():
                break

            self.logger.info(f"{self.logger_header} dummy file delete retry start")
            self.logger.info(f"{self.logger_header} timeout {self.retry_sleep}")

            dummy_file.unlink(missing_ok=True)

            self.logger.warn(f"{self.logger_header} msg:Executed temporary file deletion retry.")
            self.logger.info(f"{self.logger_header} delete retry end")