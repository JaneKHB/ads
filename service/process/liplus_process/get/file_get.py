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
from service.common.common_service import check_unknown, rmdir_func, check_capacity
from service.db.db_service import db_file_download_log
from service.http.request import esp_download
from service.ini.ini_service import get_ini_value
from service.security.security_service import security_info


class LiplusFileGet:
    def __init__(self, logger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = LIPLUS_CURRENT_DIR
        self.tool_df = LiplusFileGet.get_tool_info(self.pno)

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

    @staticmethod
    def get_tool_info(pno):
        file_path = LIPLUS_TOOL_CSV % pno
        skiprows = int(get_ini_value(config_ini, "LIPLUS", "LIPLUS_TOOL_INFO_SKIP_LINE"))
        tool_df = pd.read_csv(file_path, encoding='shift_jis', skiprows=skiprows, sep=',', index_col=False)
        col_count = int(tool_df.shape[1])
        if col_count == 7:
            tool_df = pd.read_csv(file_path, names=LIPLUS_TOOL_INFO_HEADER_7, dtype=LIPLUS_TOOL_DATA_TYPE_7,
                                  encoding='shift_jis', skiprows=skiprows, sep=',', index_col=False)
            tool_df["reg_folder"] = ""
        else:
            tool_df = pd.read_csv(file_path, names=LIPLUS_TOOL_INFO_HEADER, dtype=LIPLUS_TOOL_DATA_TYPE,
                                  encoding='shift_jis', skiprows=skiprows, sep=',', index_col=False)

        return tool_df

    def start(self):
        # Capacity Check
        if not check_capacity("LiplusGet"):
            return

        # Processing Start Time
        start_time_collection_loop = time.time()

        for _, elem in self.tool_df.iterrows():
            # Mainが緊急終了状態
            # if get_redis_global_status(D_REDIS_SHUTDOWN_KEY) == D_SHUTDOWN:
            #     break

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
        self.logger.info(f"Total time for the collection process:{(end_time_collection_loop - start_time_collection_loop):.2f}[sec] ")

    def liplus_get_tool(self, ca_name, toolid, espaddr, cntlmt, userid, userpasswd, reg_folder):
        self.ca_name = ca_name
        self.toolid = toolid  # 装置名 (MachineName)
        self.espaddr = espaddr  # 接続先ESPアドレス (ESP Address)
        self.cntlmt = cntlmt  # ダウンロード上限数 (Download Limit)
        self.userid = userid  # ユーザID (User Id)
        self.userpasswd = userpasswd  # ユーザパスワード (User Password)

        self.logger.info(f"{self.toolid} liplus_get_tool start!!")

        protocol = "http"
        time_second = int(get_ini_value(config_ini, "LIPLUS", "LIPLUS_ESP_HTTP_TIME_OUT"))
        liplus_get_log_path = os.path.dirname(FILE_LOG_LIPLUS_GET_PATH)

        # Liplus Data Download Folder
        if reg_folder == "":
            self.reg_folder = LIPLUS_REG_FOLDER_DEFAULT + "/" + self.toolid

        # Liplus Data Temp Folder
        reg_folder_tmp = LIPLUS_REG_FOLDER_TMP + "/" + f"{self.toolid}_Get"

        # Check wget
        checkWget = subprocess.call(['wget', '-V'], stdin=None, stdout=subprocess.DEVNULL, stderr=None, shell=True)
        if checkWget != 0:
            self.logger.error("errorcode:1000 msg:Wget command does not exist.")
            return

        # Check 7zip
        check7zip = subprocess.call(['7z', "i"], stdin=None, stdout=subprocess.DEVNULL, stderr=None, shell=True)
        if check7zip != 0:
            self.logger.error("errorcode:1001 msg:7Zip command does not exist.")
            return

        # Make Liplus Data temp Folder
        if not os.path.exists(reg_folder_tmp):
            self.logger.info(f"mkdir reg_folder_tmp '{reg_folder_tmp}'")
            os.makedirs(reg_folder_tmp)

        # Make Liplus Data Download Folder
        if not os.path.exists(self.reg_folder):
            self.logger.info(f"mkdir reg_folder '{self.reg_folder}'")
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

        self.logger.info(f"{self.toolid} download URL : {base_url}")
        self.logger.info(f"{self.toolid} next URL : {next_url}")
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
            rtn = esp_download(self.logger, base_url, fname, time_second, self.twofactor, self.retry_max, self.retry_sleep)

            # If File Download fail after retrying, Loop End
            if rtn != D_SUCCESS:
                self.logger.error(f"errorcode:2000 msg:Failed to retry collecting {fname} from ESP")
                break

            tick_download_end = time.time() - tick_download_start

            # Check File is Last. If Unknown returns, File is last. There are no more files to take.
            if check_unknown(fname):
                self.logger.info(f"findstr \"Unknown\": true. '{fname}'")
                break
            else:
                self.logger.info(f"findstr \"Unknown\": false. '{fname}'")

            # Unzip Downloaded File
            tick_7zip_start = time.time()
            process_arg = ['7z', 'x', '-aoa', f'-o{reg_folder_tmp}', fname]
            self.logger.info(f"unzip command: {process_arg}")

            unzip_subprocess = subprocess.Popen(process_arg, shell=True, stdout=subprocess.PIPE)
            output = unzip_subprocess.communicate()[0]   # waiting process(unzip) to end
            unzip_ret = unzip_subprocess.returncode
            self.logger.info(output.decode())   # unzip logging

            # if unzip success, 0 returned.
            if unzip_ret != 0:
                self.logger.warn("The zip file is corrupted.")
                break   # if unzip fail, then loop end

            # Unzipping time
            tick_7zip_end = time.time() - tick_7zip_start
            self.logger.info(f"unzipping time of a {fname}:{tick_7zip_end:.3f}[sec]")

            # Logging downloaded files
            size_bytes = os.path.getsize(fname)
            db_file_download_log(self.pname, self.sname, self.pno, fname, size_bytes, tick_download_end)
            self.logger.info(f"{fname} file size = {size_bytes} bytes")

            # Call collection files next url
            dummy_fname = f"{self.current_dir}dummy_{self.toolid}"
            rtn = esp_download(self.logger, next_url, dummy_fname, time_second, self.twofactor, self.retry_max,
                               self.retry_sleep)

            # If File Next fail after retrying, Logging message.
            if rtn != D_SUCCESS:
                self.logger.error(f"errorcode:2001 msg:Failed to retry file deletion instruction to ESP.")

            # Move the Liplus data(zip) to REG_FOLDER.
            shutil.move(fname, self.reg_folder)

            # List of files in reg_folder_tmp
            list_dir = os.listdir(reg_folder_tmp)
            self.logger.info(f"dir {reg_folder_tmp} : {list_dir}")

            # khb. 삭제하는 코드가 잘못들어간건지 bat 확인해봐야함. 여러개의 파일을 다운로드 받아야하는데 폴더를 미리 삭제해버림!
            # Remove reg_folder_tmp
            # self.logger.info(f"rmdir {reg_folder_tmp}")
            # rmdir_func(self.logger, reg_folder_tmp)

            # Loop End

        # List of files in reg_folder_tmp
        list_dir = os.listdir(reg_folder_tmp)
        self.logger.info(f"dir {reg_folder_tmp} : {list_dir}")

        # Remove reg_folder_tmp
        self.logger.info(f"rmdir {reg_folder_tmp}")
        rmdir_func(self.logger, reg_folder_tmp)

        self.logger.info(f"LiplusGet_Tool Finished")


    def write_to_file(self, file_name, content):
        with open(file_name, 'w') as log_file:
            log_file.write(content)
