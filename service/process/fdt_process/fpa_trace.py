"""
=========================================================================================
 :mod:`fpa_trace` --- 。
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

from config.app_config import D_SUCCESS, config_ini, D_ERROR, FDT_CURRENT_DIR, FDT_FPA_TRACE_REG_FOLDER, SECURITYINFO_PATH, D_SHUTDOWN, D_UNKNOWN_ERROR_NO, D_REDIS_SHUTDOWN_KEY
from service.db.db_service import db_file_download_log
from service.ini.ini_service import get_ini_value
from service.common.common_service import check_unknown, remove_files_in_folder
from service.logger.db_logger_service import DbLogger
from service.process.fdt_process.file_download import FdtFileDownload
from service.redis.redis_service import get_redis_global_status
from service.remote.remote_service import remote_ssh_command, remote_scp_send_files, remote_check_path_by_sshkey
from service.http.request import esp_download
from service.security.security_service import security_info


class FdtFpaTrace:
    def __init__(self, logger: DbLogger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.manual_upload = get_ini_value(config_ini, "EEC", "EEC_FPA_MANUAL_UPLOAD")
        self.current_dir = FDT_CURRENT_DIR  # C:\\ADS\\fdt_batch
        self.tool_df = FdtFileDownload.get_tool_info(get_ini_value(config_ini, "EEC", "EEC_TOOL_INFO_COM_ERR_SKIP_LINE"))

        # :: FPATrace用コピー先サーバーのIPアドレス
        self.fpa_user = get_ini_value(config_ini, "EEC", "EEC_FPA_TRACE_USER")
        self.fpatrace_ip = get_ini_value(config_ini, "EEC", "EEC_FPA_TRACE_IP")
        self.fpatrace_dir = get_ini_value(config_ini, "EEC", "EEC_FPA_TRACE_DIR")

        self.logtitle = get_ini_value(config_ini, "EEC", "EEC_FPA_TRACE_LOGTITLE")  # C6_AUXCF_
        self.reg_folder = FDT_FPA_TRACE_REG_FOLDER

        self.cntlmt = 4  # ダウンロード上限数
        self.retry_max = 5  # rem リトライ上限
        self.retry_sleep = 2  # rem リトライ時のスリープ時間
        self.sshkey_path = get_ini_value(config_ini, "SECURITY", "SSHKEY_PATH")

        # REM 2要素認証の利用有無を判別
        self.securityinfo_path = SECURITYINFO_PATH
        self.securitykey_path = get_ini_value(config_ini, "SECURITY", "SECURITYKEY_PATH")
        self.twofactor = {}

        self.toolid = None  # 装置名
        self.modelid = None
        self.espaddr = None  # 接続先ESPアドレス
        self.userid = None  # ユーザID
        self.userpasswd = None  # ユーザパスワード

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
            # 	call %CURRENT_DIR%script\fpatrace_DL_MV.bat C6_AUXCF_ %%i %%j %%k c:\ADS\var\fpatrace %%p %%q %FPATRACE_IP% %FPATRACE_DIR%

            if self.manual_upload == '0':
                self.fpa_trace_dl_mv(elem.get('toolid'), elem.get('modelid'), elem.get('espaddr'), elem.get('userid'), elem.get('userpasswd'))
            else:
                self.fpa_trace_dl_mv_mu(elem.get('toolid'), elem.get('modelid'), elem.get('espaddr'), elem.get('userid'), elem.get('userpasswd'))

    def fpa_trace_dl_mv(self, toolid, modelid, espaddr, userid, userpasswd):
        """
        ファイルダウンロードする子スクリプト

        :param toolid:
        :param modelid:
        :param espaddr:
        :param userid:
        :param userpasswd:
        """
        self.toolid = toolid  # 装置名
        self.modelid = modelid
        self.espaddr = espaddr  # 接続先ESPアドレス
        self.userid = userid  # ユーザID
        self.userpasswd = userpasswd  # ユーザパスワード

        protocol = "http"  # REM wget時のプロトコルを設定
        time_second = int(get_ini_value(config_ini, "EEC", "EEC_ESP_HTTP_TIME_OUT"))  # REM wget時のタイムアウトまでの秒数を設定
        
        # rem 6300機種以外は終了
        if self.modelid != 1:
            return

        # REM check folder
        os.makedirs(self.reg_folder, exist_ok=True)

        # REM 2要素認証の利用有無を判別
        rtn, self.twofactor = security_info(self.logger, self.espaddr, self.securityinfo_path, self.securitykey_path)
        if rtn == D_SUCCESS and len(self.twofactor):
            protocol = "https"
            time_second = int(get_ini_value(config_ini, "EEC", "EEC_ESP_HTTPS_TIME_OUT"))  # REM wget時のタイムアウトまでの秒数を設定
        elif rtn != D_SUCCESS:
            return

        # rem ファイルダウンロードパスを出力
        url = f"{protocol}://{self.espaddr}/FileServiceCollectionAgent/Download"
        parameter = f"USER={self.userid}&PW={self.userpasswd}&ID=CollectionPlan_{self.logtitle}{self.toolid}-01"
        base_url = url + "?" + parameter
        next_url = url + "?" + parameter + "&NEXT=1"

        fname = None
        rtn = None
        self.logger.info(f"{self.toolid} download start!!")

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
                self.logger.error(f"[adslog] ERROR errorcode:2000 msg:Failed to retry collecting {fname} from ESP..")
                break
            tick_download_end = time.time() - tick_download_start

            # REM ファイルが最後かどうか確認する。Unknownが返ってきた場合はもう取るファイルは無い。
            if check_unknown(fname):
                self.logger.info("Unknownが返ってきた場合はループから抜ける")
                break

            # REM ### ZIPファイルを解凍する ####
            tick_7zip_start = time.time()
            process_arg = ['7z', 'x', '-aoa', f'-o{self.reg_folder}/{self.logtitle}{self.toolid}', fname]
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

            # rem ### 1sec. waiting ############
            time.sleep(1)
            # rtn = ping_command('localhost', 2)

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
        list_dir = os.listdir(os.path.join(self.reg_folder, f"{self.logtitle}{self.toolid}"))
        for filename in list_dir:
            self.logger.info(f"reg_folder file = {filename}")

        # REM ************************************************************
        # REM *** ファイル移動処理 ***************************************
        # REM ************************************************************
        #
        # REM *** FPA Trace用フォルダの存在確認 *******************
        rtn = remote_check_path_by_sshkey(self.logger, self.sshkey_path, self.fpa_user, self.fpatrace_ip, self.fpatrace_dir)
        if rtn != D_SUCCESS:
            self.logger.error(9001, "FPA Trace用のコピー先が見つかりません！")
            return D_ERROR

        self.logger.info(":echod file transfer starts.")
        source_folder = os.path.join(self.reg_folder, f"{self.logtitle}{self.toolid}", "*")
        rtn = remote_scp_send_files(self.sshkey_path, source_folder, self.fpa_user, self.fpatrace_ip, self.fpatrace_dir)
        if rtn == D_SUCCESS:
            # REM *** 転送成功時
            self.logger.info("transfer success. file transfer end.")
            # :execute del /q %REG_FOLDER%\%LOGTITLE%%TOOLID%\*.*
            folder = os.path.join(self.reg_folder, f"{self.logtitle}{self.toolid}")
            remove_files_in_folder(folder)
        else:
            # REM *** 転送失敗時
            self.logger.error(3000, "SCP transfer of REG_FOLDERLOGTITLETOOLID failed.")

        self.logger.info(f"file transfer end.")

    def fpa_trace_dl_mv_mu(self, toolid, modelid, espaddr, userid, userpasswd):
        pass
