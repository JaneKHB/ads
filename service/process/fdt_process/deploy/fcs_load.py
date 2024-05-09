"""
=========================================================================================
 :mod:`fcs_load` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import os
import time
from typing import Union

from config.app_config import D_SUCCESS, D_ERROR, FDT_CURRENT_DIR, FDT_ADS2_UPLOAD_DIR
from service.javaif.javaif_service import javaif_execute
from service.logger.db_logger_service import DbLogger
from service.process.fdt_process.download.file_download import FdtFileDownload
from service.remote.remote_service import remote_check_folder


class FdtFcsLoad:
    def __init__(self, logger: DbLogger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = FDT_CURRENT_DIR
        self.ads2_upload = FDT_ADS2_UPLOAD_DIR
        self.tool_df = FdtFileDownload.get_tool_info()

        self.toolid = None  # 装置名
        self.modelid = None
        self.otsipaddr = None
        self.reg_folder = None  # 正規フォルダパス d:\ADS\LOG\temp\装置名
        self.backup_dir = None
        self.wait_time = None
        self.eesp_var = None

    def start(self):
        for _, elem in self.tool_df.iterrows():
            # # Mainが緊急終了状態
            # if get_redis_global_status(D_REDIS_SHUTDOWN_KEY) == D_SHUTDOWN:
            #     break

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
            # call %CURRENT_DIR%script\FCSLoad_Tool.bat %%i %%j %%n %ADS2_UPLOAD%\%%i %%r %%s %CURRENT_DIR%

            self.fcs_load_tool(elem.get('toolid'), elem.get('modelid'), elem.get('otsipaddr'),
                               f"{self.ads2_upload}{os.sep}{elem.get('toolid')}", elem.get('backup_dir'), elem.get('wait_time'))

    def fcs_load_tool(self, toolid, modelid, otsipaddr, reg_folder, backup_dir, wait_time):
        """
        ファイルダウンロードする子スクリプト

        :return: None
        """
        self.toolid = toolid  # 装置名
        self.modelid = modelid
        self.otsipaddr = otsipaddr
        self.reg_folder = reg_folder  # 正規フォルダパス d:\ADS\LOG\Upload\装置名
        self.backup_dir = backup_dir
        self.wait_time = wait_time
        self.eesp_var = f"{self.otsipaddr}/ees"     # todo

        # REM *** デプロイ先OTSフォルダの存在確認 *******************
        # 배포 대상 OTS 폴더의 존재 확인
        rtn = remote_check_folder(self.logger, self.eesp_var)
        if rtn != D_SUCCESS:
            self.logger.error(9001, "OTS先が見つかりません！")
            return D_ERROR

        # REM *** 正規フォルダ内の0バイトファイル削除処理 *******************
        # 정규 폴더 내의 0 바이트 파일 삭제 처리
        list_dir = os.listdir(self.reg_folder)
        for filename in list_dir:
            file = self.reg_folder + os.sep + filename
            if os.path.exists(file) and os.path.isfile(file):
                size = os.path.getsize(file)
                if size == 0:
                    os.remove(file)

        # REM 正規フォルダ配下のファイル一覧表示
        # 일반 폴더 아래의 파일 목록 표시
        list_dir = os.listdir(self.reg_folder)
        for filename in list_dir:
            self.logger.info(f"reg_folder file = {filename}")

        # FCS Calling
        self.logger.info("FCS Calling")
        rtn = javaif_execute(self.logger, self.modelid, self.toolid, self.reg_folder, self.eesp_var)
        if rtn != D_SUCCESS:
            self.logger.error(9001, "javaif_execute error")

        # call :echod %WAIT_TIME% 秒　待ちます
        time.sleep(self.wait_time)

        self.logger.info("FCSLoad_Tool Finished")


if __name__ == '__main__':
    logger = DbLogger("FDT", "DEPLOY", 0)
    obj = FdtFcsLoad(logger, "FDT", "DEPLOY", 0)
    obj.start()
