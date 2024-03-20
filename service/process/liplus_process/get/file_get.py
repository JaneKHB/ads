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

from config.app_config import D_SUCCESS, config_ini, SECURITYINFO_PATH, D_SHUTDOWN, D_REDIS_SHUTDOWN_KEY, LIPLUS_CURRENT_DIR, LIPLUS_TOOL_CSV, LIPLUS_TOOL_INFO_HEADER_7, LIPLUS_TOOL_DATA_TYPE_7, LIPLUS_TOOL_INFO_HEADER, LIPLUS_TOOL_DATA_TYPE, LIPLUS_REG_FOLDER_DEFAULT, LIPLUS_REG_FOLDER_TMP
from service.common.common_service import check_unknown, rmdir_func, check_capacity
from service.db.db_service import db_file_download_log
from service.http.request import esp_download
from service.ini.ini_service import get_ini_value
from service.logger.db_logger_service import DbLogger
from service.security.security_service import security_info


class LiplusFileGet:
    def __init__(self, logger: DbLogger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = LIPLUS_CURRENT_DIR
        self.tool_df = LiplusFileGet.get_tool_info(self.pno)

        self.ca_name = None
        self.toolid = None  # 装置名
        self.espaddr = None  # 接続先ESPアドレス
        self.cntlmt = None  # ダウンロード上限数
        self.reg_folder = None  # 正規フォルダパス
        self.userid = None  # ユーザID
        self.userpasswd = None  # ユーザパスワード

        self.retry_max = 5  # rem リトライ上限
        self.retry_sleep = 2  # rem リトライ時のスリープ時間

        # REM 2要素認証の利用有無を判別
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
            tool_df = pd.read_csv(file_path, names=LIPLUS_TOOL_INFO_HEADER_7, dtype=LIPLUS_TOOL_DATA_TYPE_7, encoding='shift_jis', skiprows=skiprows, sep=',', index_col=False)
            tool_df["reg_folder"] = ""
        else:
            tool_df = pd.read_csv(file_path, names=LIPLUS_TOOL_INFO_HEADER, dtype=LIPLUS_TOOL_DATA_TYPE, encoding='shift_jis', skiprows=skiprows, sep=',', index_col=False)

        return tool_df

    def start(self):
        # REM 空き容量チェック（対象ドライブと空き容量リミット％を設定）
        # 여유 용량 체크(대상 드라이브와 여유 용량 리미트%를 설정)
        if not check_capacity("LiplusGet"):
            return

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

    def liplus_get_tool(self, ca_name, toolid, espaddr, cntlmt, userid, userpasswd, reg_folder):
        """
        ファイルダウンロードする子スクリプト

        :return: None
        """
        self.ca_name = ca_name
        self.toolid = toolid  # 装置名
        self.espaddr = espaddr  # 接続先ESPアドレス
        self.cntlmt = cntlmt  # ダウンロード上限数
        self.userid = userid  # ユーザID
        self.userpasswd = userpasswd  # ユーザパスワード
        protocol = "http"
        time_second = int(get_ini_value(config_ini, "LIPLUS", "LIPLUS_ESP_HTTP_TIME_OUT"))
        
        # rem Liplusデータ取得先フォルダ
        # Liplus 데이터 검색 대상 폴더
        if reg_folder == "":
            self.reg_folder = LIPLUS_REG_FOLDER_DEFAULT + os.sep + self.toolid

        fname = None

        # rem Liplusデータ一時取得用フォルダ
        # Liplus 데이터 임시 검색 폴더
        reg_folder_tmp = LIPLUS_REG_FOLDER_TMP + os.sep + f"{self.toolid}_Get"

        # Liplusデータ一時取得用フォルダ作成
        # Liplus 데이터 임시 취득용 폴더 작성
        os.makedirs(reg_folder_tmp, exist_ok=True)

        # Liplusデータ取得先フォルダ作成
        # Liplus 데이터 검색 대상 폴더 만들기
        os.makedirs(self.reg_folder, exist_ok=True)

        # REM 2要素認証の利用有無を判別
        rtn, self.twofactor = security_info(self.logger, self.espaddr, self.securityinfo_path, self.securitykey_path)
        if rtn == D_SUCCESS and len(self.twofactor):
            protocol = "https"
            time_second = int(get_ini_value(config_ini, "LIPLUS", "LIPLUS_ESP_HTTPS_TIME_OUT"))
        elif rtn != D_SUCCESS:
            return 

        # rem ファイルダウンロードパスを出力
        url = f"{protocol}://{self.espaddr}/FileServiceCollectionAgent/Download"
        parameter = f"USER={self.userid}&PW={self.userpasswd}&ID=CollectionPlan_{self.ca_name}-01"
        base_url = url + "?" + parameter
        next_url = url + "?" + parameter + "&NEXT=1"

        # self.logger.info(f"{self.toolid} liplus_get_tool start!!")

        # self.logger.info("base_url=" + base_url)
        # self.logger.info("next_url=" + next_url)

        # REM ループはここに戻る
        for i in range(self.cntlmt):
            # REM ダウンロードファイル名が一意になるように決定
            now = datetime.datetime.now()
            datetimenow = now.strftime("%Y%m%d%H%M%S%f")[:-4]
            fname = f"{reg_folder_tmp}{os.sep}{self.toolid}-{datetimenow}.zip"

            # REM *** 定期収集ファイルダウンロード *****************************
            tick_download_start = time.time()
            rtn = esp_download(self.logger, base_url, fname, time_second, self.twofactor, self.retry_max, self.retry_sleep)
            # REM リトライしてもファイル取れなかったらログを残して次のコレクションプランに行く
            if rtn != D_SUCCESS:
                # self.logger.error(2000, f"Failed to retry collecting {fname} from ESP..")
                print(f"Failed to retry collecting {fname} from ESP..")
                break
            tick_download_end = time.time() - tick_download_start

            # REM ファイルが最後かどうか確認する。Unknownが返ってきた場合はもう取るファイルは無い。
            if check_unknown(fname):
                # self.logger.info("Unknownが返ってきた場合はループから抜ける")
                print("Unknownが返ってきた場合はループから抜ける")
                break

            # REM ### ZIPファイルを解凍する ####
            tick_7zip_start = time.time()
            process_arg = ['7z', 'x', '-aoa', f'-o{reg_folder_tmp}', fname]
            ret = subprocess.call(process_arg, shell=True)
            # rem ZIPの解凍が失敗の場合、ERRORLEVELが0以外となる
            if ret != 0:
                # self.logger.warn("zipファイルが0バイト、もしくはzipファイルが壊れているため終了します")
                print("zipファイルが0バイト、もしくはzipファイルが壊れているため終了します")
                break
            # REM　ZIPファイルの解凍処理時間をログに出力する
            tick_7zip_end = time.time() - tick_7zip_start
            # self.logger.info(f"Execution time: {tick_7zip_end:.6f} seconds")
            print(f"Execution time: {tick_7zip_end:.6f} seconds")

            # REM ダウンロードしたファイルのサイズをログ出力する
            size_bytes = os.path.getsize(fname)
            db_file_download_log(self.pname, self.sname, self.pno, fname, size_bytes, tick_download_end)
            # self.logger.info(f"{fname} file size = {size_bytes} bytes")
            print(f"{fname} file size = {size_bytes} bytes")

            # REM *** 定期収集ファイルNEXT処理 ***********************************
            dummy_fname = f"{self.current_dir}dummy_{self.toolid}"
            rtn = esp_download(self.logger, next_url, dummy_fname, time_second, self.twofactor, self.retry_max, self.retry_sleep)
            # # REM リトライしてもファイル取れなかったらログを残して次のコレクションプランに行く
            # if rtn != D_SUCCESS:
            #     self.logger.error(2000, f"Failed to retry collecting {fname} from ESP..")
            #     break

            # REM *** 取得したLiplusデータ(zip)をREG_FOLDERに移す ***********************************
            # call :execute move /Y "%REG_FOLDER_TMP%\%FNAME%.zip" "%REG_FOLDER%"
            shutil.move(fname, self.reg_folder)

            # REM 正規フォルダ配下のファイル一覧表示
            # call :execute dir /s "%REG_FOLDER_TMP%"
            list_dir = os.listdir(reg_folder_tmp)
            for filename in list_dir:
                # self.logger.info(f"reg_folder_tmp file = {filename}")
                print(f"reg_folder_tmp file = {filename}")

            # REM *** Liplusデータ一時取得用フォルダ削除 ********
            # call :execute rmdir /s /q "%REG_FOLDER_TMP%"
            rmdir_func(self.logger, reg_folder_tmp)

            # Loop End

        # REM 正規フォルダ配下のファイル一覧表示
        list_dir = os.listdir(reg_folder_tmp)
        for filename in list_dir:
            # self.logger.info(f"reg_folder_tmp file = {filename}")
            print(f"reg_folder_tmp file = {filename}")

        # REM *** Liplusデータ一時取得用フォルダ削除 ********
        rmdir_func(self.logger, reg_folder_tmp)

        # self.logger.info(f"{self.toolid} liplus_get_tool Finished")
        print(f"{self.toolid} liplus_get_tool Finished")
