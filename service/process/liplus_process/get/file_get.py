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
import subprocess
import time
from typing import Union

import pandas as pd

from config.app_config import D_SUCCESS, config_ini, SECURITYINFO_PATH, \
    LIPLUS_CURRENT_DIR, LIPLUS_TOOL_CSV, LIPLUS_TOOL_INFO_HEADER_7, LIPLUS_TOOL_DATA_TYPE_7, LIPLUS_TOOL_INFO_HEADER, \
    LIPLUS_TOOL_DATA_TYPE, LIPLUS_REG_FOLDER_DEFAULT, LIPLUS_REG_FOLDER_TMP, FILE_LOG_LIPLUS_GET_PATH
from service.capa.capa_service import check_capacity
from service.common.common_service import check_unknown, rmdir_func, get_csv_info
from service.http.request import esp_download
from service.ini.ini_service import get_ini_value
from service.security.security_service import security_info
from service.sevenzip.sevenzip_service import unzip


class LiplusFileGet:
    def __init__(self, logger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = LIPLUS_CURRENT_DIR
        self.tool_df = get_csv_info("LIPLUS", "TRANSFER", self.pno)

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
        self.securityinfo_path = SECURITYINFO_PATH
        self.securitykey_path = get_ini_value(config_ini, "SECURITY", "SECURITYKEY_PATH")
        self.twofactor = {}

    def start(self):
        # Capacity Check
        if not check_capacity("LiplusGet"):
            return

        # Processing Start Time
        start_time_collection_loop = time.time()

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

            self.liplus_get_tool(elem.get('ca_name'), elem.get('toolid'), elem.get('espaddr'), elem.get('cntlmt'),
                                 elem.get('userid'), elem.get('userpasswd'), elem.get('reg_folder'))

        # Processing End Time
        end_time_collection_loop = time.time()

        # Processing Time logging
        logger_header = f"[{self.toolid}]"
        self.logger.info(f"{logger_header} Total time for the collection process:{(end_time_collection_loop - start_time_collection_loop):.2f}[sec] ")

    def liplus_get_tool(self, ca_name, toolid, espaddr, cntlmt, userid, userpasswd, reg_folder):
        self.ca_name = ca_name
        self.toolid = toolid  # 装置名 (MachineName)
        self.espaddr = espaddr  # 接続先ESPアドレス (ESP Address)
        self.cntlmt = cntlmt  # ダウンロード上限数 (Download Limit)
        self.userid = userid  # ユーザID (User Id)
        self.userpasswd = userpasswd  # ユーザパスワード (User Password)

        logger_header = f"[{self.toolid}]"
        self.logger.info(f"{logger_header} liplus_get_tool start!!")

        protocol = "http"
        time_second = int(get_ini_value(config_ini, "LIPLUS", "LIPLUS_ESP_HTTP_TIME_OUT"))
        liplus_get_log_path = os.path.dirname(FILE_LOG_LIPLUS_GET_PATH % self.pno)

        # Liplus Data Download Folder
        if reg_folder == "":
            self.reg_folder = LIPLUS_REG_FOLDER_DEFAULT + "/" + self.toolid

        # Liplus Data Temp Folder
        reg_folder_tmp = LIPLUS_REG_FOLDER_TMP + "/" + f"{self.toolid}_Get"

        # Check wget
        checkWget = subprocess.call(['wget', '-V'], stdin=None, stdout=subprocess.DEVNULL, stderr=None, shell=True)
        if checkWget != 0:
            self.logger.error(f"{logger_header} errorcode:1000 msg:Wget command does not exist.")
            return

        # Check 7zip
        check7zip = subprocess.call(['7z', "i"], stdin=None, stdout=subprocess.DEVNULL, stderr=None, shell=True)
        if check7zip != 0:
            self.logger.error(f"{logger_header} errorcode:1001 msg:7Zip command does not exist.")
            return

        # Make Liplus Data temp Folder
        if not os.path.exists(reg_folder_tmp):
            self.logger.info(f"{logger_header} mkdir reg_folder_tmp '{reg_folder_tmp}'")
            os.makedirs(reg_folder_tmp)

        # Make Liplus Data Download Folder
        if not os.path.exists(self.reg_folder):
            self.logger.info(f"{logger_header} mkdir reg_folder '{self.reg_folder}'")
            os.makedirs(self.reg_folder)

        # Check two Factor Auth
        rtn, self.twofactor = security_info(self.logger, self.espaddr, self.securityinfo_path, self.securitykey_path)
        if rtn == D_SUCCESS and len(self.twofactor):
            protocol = "https"
            time_second = int(get_ini_value(config_ini, "LIPLUS", "LIPLUS_ESP_HTTPS_TIME_OUT"))
        elif rtn != D_SUCCESS:
            return

        # File Download URL
        url = f"{protocol}://{self.espaddr}/FileServiceCollectionAgent/Download"
        parameter = f"USER={self.userid}&PW={self.userpasswd}&ID=CollectionPlan_{self.ca_name}-01"
        base_url = url + "?" + parameter
        next_url = url + "?" + parameter + "&NEXT=1"

        # Save the download URL as file.
        url_folder_path = liplus_get_log_path + "/" + "get_url"
        os.makedirs(url_folder_path, exist_ok=True)

        self.write_to_file(f"{url_folder_path}/{self.toolid}_DL.txt", base_url)
        self.write_to_file(f"{url_folder_path}/{self.toolid}_NXT.txt", next_url)

        # Loop Start
        for i in range(self.cntlmt):
            # Unique File Name
            now = datetime.datetime.now()
            datetimenow = now.strftime("%Y%m%d%H%M%S%f")[:-4]
            fname = f"{reg_folder_tmp}/{self.toolid}-{datetimenow}.zip"

            # Call collection files download url
            tick_download_start = time.time()

            self.logger.info(f"{logger_header} download URL : {base_url}")
            rtn = esp_download(self.logger, base_url, fname, time_second, self.twofactor, self.retry_max, self.retry_sleep)

            # If File Download fail after retrying, Loop End
            if rtn == D_SUCCESS:
                self.logger.info(f"{logger_header} download success. got zip file: {fname}")
            else:
                self.logger.error(f"{logger_header} errorcode:2000 msg:Failed to retry collecting {fname} from ESP")
                break

            tick_download_end = time.time() - tick_download_start

            # Check File is Last. If Unknown returns, File is last. There are no more files to take.
            if check_unknown(fname):
                self.logger.info(f"{logger_header} findstr \"Unknown\": true. '{fname}'")
                break
            else:
                self.logger.info(f"{logger_header} findstr \"Unknown\": false. '{fname}'")

            # Unzip Downloaded File
            tick_7zip_start = time.time()
            unzip_cmd = ['7z', 'x', '-aoa', f'-o{reg_folder_tmp}', fname]
            unzip_ret = unzip(self.logger, unzip_cmd)

            # if unzip success, 0 returned.
            if unzip_ret != 0:
                self.logger.warn(f"{logger_header} The zip file is corrupted.")
                break   # if unzip fail, then loop end

            # Unzipping time
            tick_7zip_end = time.time() - tick_7zip_start
            self.logger.info(f"{logger_header} Unzipping time of a '{fname}':{tick_7zip_end:.3f}[sec]")

            # Logging downloaded files
            size_bytes = os.path.getsize(fname)
            self.logger.info(f"{logger_header} file size = {size_bytes} bytes. '{fname}'")

            # Call collection files NEXT url
            self.logger.info(f"{logger_header} NXT URL : {next_url}")
            dummy_fname = f"{self.current_dir}dummy_{self.toolid}"
            rtn = esp_download(self.logger, next_url, dummy_fname, time_second, self.twofactor, self.retry_max,
                               self.retry_sleep)

            # If File Next fail after retrying, Logging message.
            if rtn == D_SUCCESS:
                self.logger.info(f"{logger_header} Next Request command success.")
            else:
                self.logger.error(f"{logger_header} errorcode:2001 msg:Failed to retry file deletion instruction to ESP.")

            # Move the Liplus data(zip) to REG_FOLDER.
            shutil.move(fname, self.reg_folder)

            # List of files in reg_folder_tmp
            list_dir = os.listdir(reg_folder_tmp)
            self.logger.info(f"{logger_header} dir '{reg_folder_tmp}' : {list_dir}")

            # khb. fixme: 폴더를 삭제하는 코드가 ADS_1.2에 새로 추가. ADS_1.2 bat(LiplusGet_Tool.bat)에서도 여러개의 파일을 다운로드 받아야하는데 폴더를 미리 삭제해버리면서 에러 발생!
            # Remove reg_folder_tmp
            # self.logger.info(f"rmdir {reg_folder_tmp}")
            # rmdir_func(self.logger, reg_folder_tmp)

            # Loop End

        # List of files in reg_folder_tmp
        list_dir = os.listdir(reg_folder_tmp)
        self.logger.info(f"{logger_header} dir '{reg_folder_tmp}' : {list_dir}")

        # Remove reg_folder_tmp
        self.logger.info(f"{logger_header} rmdir '{reg_folder_tmp}'")
        rmdir_func(self.logger, reg_folder_tmp)

        self.logger.info(f"{logger_header} LiplusGet_Tool Finished")


    def write_to_file(self, file_name, content):
        with open(file_name, 'w') as log_file:
            log_file.write(content)
