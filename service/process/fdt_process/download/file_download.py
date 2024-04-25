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
from service.ini.ini_service import get_ini_value
from service.common.common_service import check_unknown, get_csv_info
from service.http.request import esp_download
from service.security.security_service import security_info

# \ADS\fdt_batch\FileDownload.bat
class FdtFileDownload:
    def __init__(self, logger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.manual_upload = get_ini_value(config_ini, "EEC", "EEC_MANUAL_UPLOAD")
        self.current_dir = FDT_CURRENT_DIR
        self.tool_df = get_csv_info("FDT", "DOWNLOAD")

        self.toolid = None  # 装置名 장치명
        self.espaddr = None  # 接続先ESPアドレス 연결 대상 ESP 주소
        self.cntlmt = None  # ダウンロード上限数 다운로드 상한
        self.reg_folder = None  # 正規フォルダパス 정규 폴더 경로
        self.userid = None  # ユーザID 사용자ID
        self.userpasswd = None  # ユーザパスワード 사용자 비밀번호

        self.retry_max = 5  # rem リトライ上限 Retry 상한
        self.retry_sleep = 2  # rem リトライ時のスリープ時間 Retry interval time

        # REM 2要素認証の利用有無を判別
        # 2요소 인증의 이용 유무를 판별
        self.securityinfo_path = SECURITYINFO_PATH
        self.securitykey_path = get_ini_value(config_ini, "SECURITY", "SECURITYKEY_PATH")
        self.twofactor = {}

    def start(self):
        for _, elem in self.tool_df.iterrows():

            # PKRFG11,1,10.47.146.63:8080,4,OTST401,10.53.193.13,C:\LOG\Download\PKRFG11,inazawa.wataru,CanonCanon,C:\backup,0
            # 	rem	 1:%%i : 装置名 장치명
            # 	rem	 2:%%j : 機種ID(1:6300 / 2:従来機) 모델ID
            # 	rem	 3:%%k : 接続先ESPアドレス 연결 대상 ESP 주소
            # 	rem	 4:%%l : ダウンロード上限数 다운로드 상한
            # 	rem	 5:%%m : デプロイ先OTS名 배포 대상 OTS 이름
            # 	rem	 6:%%n : OTSのIPアドレス OTS IP주소
            # 	rem	 7:%%o : 正規フォルダパス 정규 폴더 경로
            # 	rem	 8:%%p : ログインユーザID 로그인 사용자 ID
            # 	rem	 9:%%q : ログインユーザパスワード 비밀번호
            # 	rem	10:%%r : バックアップフォルダパス（6300用）백업폴더 경로
            # 	rem	11:%%s : Wait時間 wait time
            # call %CURRENT_DIR%script\FGet_Tool.bat %%i %%k %%l %%o %%p %%q %CURRENT_DIR%

            if self.manual_upload == '0':
                self.fget_tool(elem.get('toolid'), elem.get('espaddr'), elem.get('cntlmt'),
                               elem.get('reg_folder'), elem.get('userid'), elem.get('userpasswd'))
            else:
                # 手動アップロードタイプの場合
                self.fget_tool_mu(elem.get('toolid'), elem.get('espaddr'), elem.get('cntlmt'),
                                  elem.get('reg_folder'), elem.get('userid'), elem.get('userpasswd'))

    # \ADS\fdt_batch\script\FGet_Tool.bat
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
        # 2요소 인증의 이용 유무를 판별
        rtn, self.twofactor = security_info(self.logger, self.espaddr, self.securityinfo_path, self.securitykey_path)
        if rtn == D_SUCCESS and len(self.twofactor):
            protocol = "https"
            time_second = int(get_ini_value(config_ini, "EEC", "EEC_ESP_HTTPS_TIME_OUT"))
        elif rtn != D_SUCCESS:
            return 

        # rem ファイルダウンロードパスを出力
        # 파일 다운로드 경로 출력
        url = f"{protocol}://{self.espaddr}/FileServiceCollectionAgent/Download"
        parameter = f"USER={self.userid}&PW={self.userpasswd}&ID=CollectionPlan_{self.toolid}-01"
        base_url = url + "?" + parameter
        next_url = url + "?" + parameter + "&NEXT=1"

        self.logger.info(f"{self.toolid} download start!!")

        self.logger.info("base_url=" + base_url)
        self.logger.info("next_url=" + next_url)

        # REM ループはここに戻る
        # ループはここに戻る
        for i in range(self.cntlmt):
            # REM ダウンロードファイル名が一意になるように決定
            # 다운로드 파일 이름이 고유하도록 결정
            datetimenow = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-4]
            fname = f"{self.current_dir}{self.toolid}-{datetimenow}.zip"

            # REM *** 定期収集ファイルダウンロード *****************************
            # 정기 수집 파일 다운로드
            tick_download_start = time.time()
            rtn = esp_download(self.logger, base_url, fname, time_second, self.twofactor, self.retry_max, self.retry_sleep)
            # REM リトライしてもファイル取れなかったらログを残して次のコレクションプランに行く
            # 다시 시도해도 파일을 얻을 수 없으면 로그를 남기고 다음 컬렉션 계획으로 이동하십시오.
            if rtn != D_SUCCESS:
                self.logger.error(2000, f"Failed to retry collecting {fname} from ESP..")
                break
            tick_download_end = time.time() - tick_download_start

            # REM ファイルが最後かどうか確認する。Unknownが返ってきた場合はもう取るファイルは無い。
            # 파일이 마지막인지 확인합니다. Unknown이 돌아왔을 경우는 더 이상 취할 파일은 없다.
            if check_unknown(fname):
                self.logger.info("Unknownが返ってきた場合はループから抜ける")
                break

            # REM ### ZIPファイルを解凍する ####
            # ZIP 파일 압축 해제
            tick_7zip_start = time.time()
            process_arg = ['7z', 'x', '-aoa', f'-o{self.reg_folder}', fname]
            ret = subprocess.call(process_arg, shell=True)
            # rem ZIPの解凍が失敗の場合、ERRORLEVELが0以外となる
            # ZIP 압축이 풀리면 ERRORLEVEL이 0이 아닙니다.
            if ret != 0:
                self.logger.warn("zipファイルが0バイト、もしくはzipファイルが壊れているため終了します")
                break
            # REM　ZIPファイルの解凍処理時間をログに出力する
            # ZIP 파일의 압축 해제 시간을 로그에 출력
            tick_7zip_end = time.time() - tick_7zip_start
            self.logger.info(f"Execution time: {tick_7zip_end:.6f} seconds")

            # REM ダウンロードしたファイルのサイズをログ出力する
            # 다운로드한 파일의 크기를 로깅
            size_bytes = os.path.getsize(fname)
            self.logger.info(f"{fname} file size = {size_bytes} bytes")

            # REM *** ZIPファイルを削除 ******************************************
            # ZIP 파일 삭제
            if os.path.exists(fname):
                os.remove(fname)

            # REM *** 定期収集ファイルNEXT処理 ***********************************
            # 정기 수집 파일 NEXT 처리
            dummy_fname = f"{self.current_dir}dummy_{self.toolid}"
            rtn = esp_download(self.logger, next_url, dummy_fname, time_second, self.twofactor, self.retry_max, self.retry_sleep)
            # # REM リトライしてもファイル取れなかったらログを残して次のコレクションプランに行く
            # 다시 시도해도 파일을 얻을 수 없으면 로그를 남기고 다음 컬렉션 계획으로 이동하십시오.
            # if rtn != D_SUCCESS:
            #     self.logger.error(2000, f"Failed to retry collecting {fname} from ESP..")
            #     break

            # REM *** 一時ファイル削除処理 ***********************************
            # 임시 파일 삭제 처리
            if os.path.exists(dummy_fname):
                os.remove(dummy_fname)

            # Loop End

        # REM *** 正常シーケンス以外でのダウンロードファイル削除処理 ********
        # 정상 시퀀스 이외의 다운로드 파일 삭제 처리
        if fname is not None and os.path.exists(fname):
            os.remove(fname)

        # REM 正規フォルダ配下のファイル一覧表示
        # 일반 폴더 아래의 파일 목록 표시
        list_dir = os.listdir(self.reg_folder)
        for filename in list_dir:
            self.logger.info(f"reg_folder file = {filename}")

        self.logger.info(f"{self.toolid} FGet_Tool Finished")

    def fget_tool_mu(self, toolid, espaddr, cntlmt, reg_folder, userid, userpasswd):

        self.toolid = toolid  # 装置名
        self.espaddr = espaddr  # 接続先ESPアドレス
        self.cntlmt = cntlmt  # ダウンロード上限数
        self.reg_folder = reg_folder  # 正規フォルダパス
        self.userid = userid  # ユーザID
        self.userpasswd = userpasswd  # ユーザパスワード

        pass
