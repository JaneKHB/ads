"""
=========================================================================================
 :mod:`file_download` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import datetime
import os
import subprocess
import time
from typing import Union

import pandas as pd

from config.app_config import D_SUCCESS, config_ini, FDT_TOOL_INFO_HEADER, FDT_TOOL_DATA_TYPE, FDT_CURRENT_DIR, FDT_TOOL_CSV, SECURITYINFO_PATH, D_SHUTDOWN, D_UNKNOWN_ERROR_NO, D_REDIS_SHUTDOWN_KEY
from service.db.db_service import db_file_download_log
from service.ini.ini_service import get_ini_value
from service.logger.db_logger_service import DbLogger
from service.common.common_service import check_unknown
from service.redis.redis_service import get_redis_global_status
from service.http.request import esp_download
from service.security.security_service import security_info


class FdtFileDownload:
    def __init__(self, logger: DbLogger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.manual_upload = get_ini_value(config_ini, "EEC", "EEC_MANUAL_UPLOAD")
        self.current_dir = FDT_CURRENT_DIR
        self.tool_df = FdtFileDownload.get_tool_info(get_ini_value(config_ini, "EEC", "EEC_TOOL_INFO_COM_ERR_SKIP_LINE"))

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
    def get_tool_info(skiprows_str=None):
        file_path = FDT_TOOL_CSV
        if skiprows_str is None:
            skiprows = int(get_ini_value(config_ini, "EEC", "EEC_TOOL_INFO_SKIP_LINE"))
        else:
            skiprows = int(skiprows_str)
        tool_df = pd.read_csv(file_path, names=FDT_TOOL_INFO_HEADER, dtype=FDT_TOOL_DATA_TYPE, encoding='shift_jis', skiprows=skiprows, sep=',', index_col=False)
        return tool_df

    def start(self):
        for _, elem in self.tool_df.iterrows():
            # Mainが緊急終了状態
            if get_redis_global_status(D_REDIS_SHUTDOWN_KEY) == D_SHUTDOWN:
                break

            # PKRFG11,1,10.47.146.63:8080,4,OTST401,10.53.193.13,C:\LOG\Download\PKRFG11,inazawa.wataru,CanonCanon,C:\backup,0
            # 	rem	 1:%%i : 装置名
            # 	rem	 2:%%j : 機種ID(1:6300 / 2:従来機)
            # 	rem	 3:%%k : 接続先ESPアドレス
            # 	rem	 4:%%l : ダウンロード上限数
            # 	rem	 5:%%m : デプロイ先OTS名
            # 	rem	 6:%%n : OTSのIPアドレス
            # 	rem	 7:%%o : 正規フォルダパス
            # 	rem	 8:%%p : ログインユーザID
            # 	rem	 9:%%q : ログインユーザパスワード
            # 	rem	10:%%r : バックアップフォルダパス（6300用）
            # 	rem	11:%%s : Wait時間
            # call %CURRENT_DIR%script\FGet_Tool.bat %%i %%k %%l %%o %%p %%q %CURRENT_DIR%
            
            if self.manual_upload == '0':
                self.fget_tool(elem.get('toolid'), elem.get('espaddr'), elem.get('cntlmt'),
                               elem.get('reg_folder'), elem.get('userid'), elem.get('userpasswd'))
            else:
                # 手動アップロードタイプの場合
                self.fget_tool_mu(elem.get('toolid'), elem.get('espaddr'), elem.get('cntlmt'),
                                  elem.get('reg_folder'), elem.get('userid'), elem.get('userpasswd'))

    def fget_tool(self, toolid, espaddr, cntlmt, reg_folder, userid, userpasswd):
        """
        ファイルダウンロードする子スクリプト

        :return: None
        """
        self.toolid = toolid  # 装置名
        self.espaddr = espaddr  # 接続先ESPアドレス
        self.cntlmt = cntlmt  # ダウンロード上限数
        self.reg_folder = reg_folder  # 正規フォルダパス
        self.userid = userid  # ユーザID
        self.userpasswd = userpasswd  # ユーザパスワード
        protocol = "http"
        time_second = int(get_ini_value(config_ini, "EEC", "EEC_ESP_HTTP_TIME_OUT"))
        
        fname = None

        # REM check folder
        os.makedirs(self.reg_folder, exist_ok=True)

        # REM 2要素認証の利用有無を判別
        rtn, self.twofactor = security_info(self.logger, self.espaddr, self.securityinfo_path, self.securitykey_path)
        if rtn == D_SUCCESS and len(self.twofactor):
            protocol = "https"
            time_second = int(get_ini_value(config_ini, "EEC", "EEC_ESP_HTTPS_TIME_OUT"))
        elif rtn != D_SUCCESS:
            return 

        # rem ファイルダウンロードパスを出力
        url = f"{protocol}://{self.espaddr}/FileServiceCollectionAgent/Download"
        parameter = f"USER={self.userid}&PW={self.userpasswd}&ID=CollectionPlan_{self.toolid}-01"
        base_url = url + "?" + parameter
        next_url = url + "?" + parameter + "&NEXT=1"

        self.logger.info(f"{self.toolid} download start!!")

        self.logger.info("base_url=" + base_url)
        self.logger.info("next_url=" + next_url)

        # REM ループはここに戻る
        for i in range(self.cntlmt):
            # REM ダウンロードファイル名が一意になるように決定
            now = datetime.datetime.now()
            datetimenow = now.strftime("%Y%m%d%H%M%S%f")[:-4]
            fname = f"{self.current_dir}{self.toolid}-{datetimenow}.zip"

            # REM *** 定期収集ファイルダウンロード *****************************
            tick_download_start = time.time()
            rtn = esp_download(self.logger, base_url, fname, time_second, self.twofactor, self.retry_max, self.retry_sleep)
            # REM リトライしてもファイル取れなかったらログを残して次のコレクションプランに行く
            if rtn != D_SUCCESS:
                self.logger.error(2000, f"Failed to retry collecting {fname} from ESP..")
                break
            tick_download_end = time.time() - tick_download_start

            # REM ファイルが最後かどうか確認する。Unknownが返ってきた場合はもう取るファイルは無い。
            if check_unknown(fname):
                self.logger.info("Unknownが返ってきた場合はループから抜ける")
                break

            # REM ### ZIPファイルを解凍する ####
            tick_7zip_start = time.time()
            process_arg = ['7z', 'x', '-aoa', f'-o{self.reg_folder}', fname]
            ret = subprocess.call(process_arg, shell=True)
            # rem ZIPの解凍が失敗の場合、ERRORLEVELが0以外となる
            if ret != 0:
                self.logger.warn("zipファイルが0バイト、もしくはzipファイルが壊れているため終了します")
                break
            # REM　ZIPファイルの解凍処理時間をログに出力する
            tick_7zip_end = time.time() - tick_7zip_start
            self.logger.info(f"Execution time: {tick_7zip_end:.6f} seconds")

            # REM ダウンロードしたファイルのサイズをログ出力する
            size_bytes = os.path.getsize(fname)
            db_file_download_log(self.pname, self.sname, self.pno, fname, size_bytes, tick_download_end)
            self.logger.info(f"{fname} file size = {size_bytes} bytes")

            # REM *** ZIPファイルを削除 ******************************************
            if os.path.exists(fname):
                os.remove(fname)

            # REM *** 定期収集ファイルNEXT処理 ***********************************
            dummy_fname = f"{self.current_dir}dummy_{self.toolid}"
            rtn = esp_download(self.logger, next_url, dummy_fname, time_second, self.twofactor, self.retry_max, self.retry_sleep)
            # # REM リトライしてもファイル取れなかったらログを残して次のコレクションプランに行く
            # if rtn != D_SUCCESS:
            #     self.logger.error(2000, f"Failed to retry collecting {fname} from ESP..")
            #     break

            # REM *** 一時ファイル削除処理 ***********************************
            if os.path.exists(dummy_fname):
                os.remove(dummy_fname)

            # Loop End

        # REM *** 正常シーケンス以外でのダウンロードファイル削除処理 ********
        if fname is not None and os.path.exists(fname):
            os.remove(fname)

        # REM 正規フォルダ配下のファイル一覧表示
        list_dir = os.listdir(self.reg_folder)
        for filename in list_dir:
            self.logger.info(f"reg_folder file = {filename}")

        self.logger.info(f"{self.toolid} FGet_Tool Finished")

    def fget_tool_mu(self, toolid, espaddr, cntlmt, reg_folder, userid, userpasswd):
        pass
