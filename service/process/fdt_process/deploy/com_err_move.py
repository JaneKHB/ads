"""
=========================================================================================
 :mod:`com_err_move` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import os
import shutil

from config.app_config import FDT_CURRENT_DIR, FDT_ADS2_UPLOAD_DIR
from service.logger.db_logger_service import DbLogger
from service.process.fdt_process.download.file_download import FdtFileDownload


class FdtComErrMove:
    def __init__(self, logger: DbLogger, pname, sname, pno: int):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = FDT_CURRENT_DIR
        self.ads2_upload = FDT_ADS2_UPLOAD_DIR
        self.tool_df = FdtFileDownload.get_tool_info()

        self.toolid = None  # 装置名
        self.modelid = None
        self.reg_folder = None  # 正規フォルダパス d:\ADS\LOG\temp\装置名

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
            # call %CURRENT_DIR%script\ComErrMove_Tool.bat %%i %%j %ADS2_UPLOAD%\%%i %CURRENT_DIR%
            self.com_err_move_tool(elem.get('toolid'), elem.get('modelid'), f"{self.ads2_upload}{os.sep}{elem.get('toolid')}")

    def com_err_move_tool(self, toolid, modelid, reg_folder):
        """
        ファイルダウンロードする子スクリプト

        :return: None
        """
        self.toolid = toolid  # 装置名
        self.modelid = modelid
        self.reg_folder = reg_folder  # 正規フォルダパス d:\ADS\LOG\Upload\装置名

        # REM *** 従来機のCOM／ERRログを移動させる ********************
        # 기존 기기의 COM/ERR 로그 이동
        if self.modelid == 2:
            self.logger.info("ComErrMove Start!")

            # rem フォルダが無い場合は作成する
            # 폴더가 없으면 만들기
            if not os.path.exists(f"{self.reg_folder}_ComErr"):
                os.mkdir(f"{self.reg_folder}_ComErr")

            # rem COMファイルがあったら移動させる
            # COM 파일이 있으면 이동
            # rem ERRファイルがあったら移動させる
            # ERR 파일이 있으면 이동
            list_dir = os.listdir(self.reg_folder)
            for filename in list_dir:
                file = self.reg_folder + os.sep + filename
                if os.path.isfile(file) and file.endswith("CONS_COM_com.log.gz") or file.endswith("CONS_ERR_err.log.gz"):
                    shutil.move(file, f"{self.reg_folder}_ComErr")

            self.logger.info("ComErrMove Finished!")
