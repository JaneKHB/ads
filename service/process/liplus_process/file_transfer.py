"""
=========================================================================================
 :mod:`file_transfer` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import os
import subprocess
import time
from typing import Union

from config.app_config import D_SUCCESS, D_ERROR, D_REDIS_SHUTDOWN_KEY, D_SHUTDOWN, LIPLUS_CURRENT_DIR, LIPLUS_REG_FOLDER_DEFAULT, config_ini
from service.common.common_service import remove_files_in_folder
from service.ini.ini_service import get_ini_value
from service.logger.db_logger_service import DbLogger
from service.process.liplus_process.file_get import LiplusFileGet
from service.redis.redis_service import get_redis_global_status
from service.remote.remote_service import remote_check_path_by_sshkey, remote_scp_send_files


class LiplusFileTransfer:
    def __init__(self, logger: DbLogger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = LIPLUS_CURRENT_DIR
        self.tool_df = LiplusFileGet.get_tool_info(self.pno)
        self.sshkey_path = get_ini_value(config_ini, "SECURITY", "SSHKEY_PATH")

        self.toolid = None  # 装置名
        self.reg_folder = None  # 正規フォルダパス d:\ADS\LOG\temp\装置名

    def start(self):
        for _, elem in self.tool_df.iterrows():
            # Mainが緊急終了状態
            if get_redis_global_status(D_REDIS_SHUTDOWN_KEY) == D_SHUTDOWN:
                break

            # 	rem	--------------------------------------------------------------
            # 	rem	設定ファイル「LiplusToolInfo.csv」から、
            # 	rem	一行ずつ読み込んで、必要項目を取得する
            # 	rem	--------------------------------------------------------------
            # 	rem	 2:%%i : 装置名
            # 	rem	 5:%%j : LiplusDBのIPアドレス\LiplusDBサーバのデータ転送先
            # 	rem	 8:%%k : ADSサーバー内の保存先パス
            # 	rem	--------------------------------------------------------------
            #
            # 	call %CURRENT_DIR%script\LiplusTransfer_Tool.bat %%i %%j "%%k" %CURRENT_DIR%

            self.liplus_transfer_tool(elem.get('toolid'), elem.get('ldb_dir'), elem.get('reg_folder'))

    def liplus_transfer_tool(self, toolid, ldb_dir, reg_folder):
        """
        ファイルダウンロードする子スクリプト

        :return: None
        """
        self.toolid = toolid  # 装置名
        self.ldb_dir = ldb_dir
        self.reg_folder = reg_folder  # 正規フォルダパス d:\ADS\LOG\Upload\装置名

        # for /f "tokens=1,2* delims=/" %%I in ("%LDB_DIR:\=/%") do (
        #     set REMOTE_LIPLUS_IP=%%I
        #     set REMOTE_LIPLUS_DIR=/liplus/%%K
        # )
        # todo
        remote_liplus_ip = "10.1.31.163"
        remote_liplus_dir = "/liplus/original_data/KIOXIA/3119008"
        ldb_user = get_ini_value(config_ini, "LIPLUS", "LIPLUS_LDB_USER")

        # rem Liplusデータ取得先フォルダ
        if reg_folder == "":
            self.reg_folder = LIPLUS_REG_FOLDER_DEFAULT + os.sep + self.toolid

        # rem debug --------------
        self.logger.info(f"TOOLID : {self.toolid}")
        self.logger.info(f"REMOTE_LIPLUS_IP : {remote_liplus_ip}")
        self.logger.info(f"REMOTE_LIPLUS_DIR : {remote_liplus_dir}")
        self.logger.info(f"REG_FOLDER : {self.reg_folder}")

        # REM *** Liplusデータ取得元フォルダの存在確認 *******************
        if not os.path.exists(self.reg_folder):
            self.logger.error(9001, "アップロード対象フォルダが見つかりません！処理を終了します。")

        # REM *** LiplusDBサーバアップロード先フォルダの存在確認 *******************
        rtn = remote_check_path_by_sshkey(self.logger, self.sshkey_path, ldb_user, remote_liplus_ip, remote_liplus_dir)
        if rtn != D_SUCCESS:
            self.logger.error(9001, "LiplusDBサーバ上にコピー先フォルダが見つかりません！処理を終了します。")
            return D_ERROR

        self.logger.info(f"{self.toolid} LiplusTransfer_Tool.bat start!!")
        list_dir = os.listdir(self.reg_folder)
        for filename in list_dir:
            file = self.reg_folder + os.sep + filename
            unzip_dir = self.reg_folder + os.sep + filename + "_temp"

            # REM ### ZIPファイルを解凍する ####
            tick_7zip_start = time.time()
            process_arg = ['7z', 'x', '-aoa', f'-o{unzip_dir}', file]
            ret = subprocess.call(process_arg, shell=True)
            # rem ZIPの解凍が失敗の場合、ERRORLEVELが0以外となる
            if ret != 0:
                # REM ### 異常ファイル(欠けてる場合や0バイトなど)はループから抜ける ###
                self.logger.warn("zipファイルが0バイト、もしくはzipファイルが壊れているため終了します")
                break
            # REM　ZIPファイルの解凍処理時間をログに出力する
            tick_7zip_end = time.time() - tick_7zip_start
            self.logger.info(f"Execution time: {tick_7zip_end:.6f} seconds")

            # REM ZIPファイル削除 todo 원본은 여기서 지우는데 올바를까?
            if os.path.exists(file):
                os.remove(file)

            # file transfer starts.
            self.logger.info(":echod file transfer starts.")
            source_dir = os.path.join(unzip_dir, "*")
            rtn = remote_scp_send_files(self.sshkey_path, source_dir, ldb_user, remote_liplus_ip, remote_liplus_dir)
            if rtn == D_SUCCESS:
                # REM *** 転送成功時
                self.logger.info("transfer success. file transfer end.")
                # REM *** 解凍したフォルダを削除
                # call :execute rmdir /S /Q !UNZIP_DIR!
                remove_files_in_folder(unzip_dir)
            else:
                # REM *** 転送失敗時
                self.logger.error(3000, "SCP transfer of unzip_dir failed.")
                # REM *** 解凍したフォルダを削除
                # call :execute rmdir /S /Q !UNZIP_DIR!
                remove_files_in_folder(unzip_dir)

        self.logger.info("LiplusTransfer_Tool.bat Finished")
