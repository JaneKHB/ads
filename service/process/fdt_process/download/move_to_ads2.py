"""
=========================================================================================
 :mod:`move_to_ads2` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import os
import shutil
from typing import Union

from config.app_config import D_ERROR, D_SUCCESS, config_ini, FDT_CURRENT_DIR, D_SHUTDOWN, FDT_ADS2_FOLDER_DIR, D_REDIS_SHUTDOWN_KEY
from service.zip.gz_service import gz_compress
from service.ini.ini_service import get_ini_value
from service.logger.db_logger_service import DbLogger
from service.process.fdt_process.download.file_download import FdtFileDownload
from service.redis.redis_service import get_redis_global_status


class FdtMoveToAds2:
    def __init__(self, logger: DbLogger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = FDT_CURRENT_DIR
        self.ads2_folder = FDT_ADS2_FOLDER_DIR  # "C:\\ADS\\LOG\\temp"
        self.tool_df = FdtFileDownload.get_tool_info(get_ini_value(config_ini, "EEC", "EEC_TOOL_INFO_COM_ERR_SKIP_LINE"))

        self.toolid = None  # 装置名 장치이름
        self.reg_folder = None  # 正規フォルダパス 정규 폴더 경로
        self.modelid = None # 모델ID

    def start(self):
        for _, elem in self.tool_df.iterrows():
            # Mainが緊急終了状態
            if get_redis_global_status(D_REDIS_SHUTDOWN_KEY) == D_SHUTDOWN:
                break

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
            # 	call %CURRENT_DIR%script\MoveToADS2_Tool.bat %%i %%o %CURRENT_DIR% %ADS2_FOLDER% %%j

            self.move_to_ads2_tool(elem.get('toolid'), elem.get('reg_folder'), elem.get('modelid'))

    def move_to_ads2_tool(self, toolid, reg_folder, modelid):
        """
        ファイルダウンロードする子スクリプト

        :return: None
        """
        self.toolid = toolid  # 装置名
        self.reg_folder = reg_folder  # 正規フォルダパス
        self.modelid = modelid

        # REM *** 正規フォルダの存在確認 ***************************
        # 정규 폴더의 존재 확인
        if not os.path.exists(self.reg_folder):
            self.logger.warn(f"reg_folder {self.reg_folder}フォルダが見つかりません！")
            return D_SUCCESS

        # REM *** ADS2の渡し先フォルダの存在確認 *******************
        if not os.path.exists(self.ads2_folder):
            self.logger.error(9001, f"ads2_folder {self.ads2_folder}フォルダが見つかりません！")
            return D_ERROR

        self.logger.info(f"{self.toolid} MoveToADS2_Tool start!!")

        # rem もしフォルダがあった場合はまだFCS側処理にいってないので、何もしないで終了
        # 폴더가있는 경우 아직 FCS 측 처리에 있지 않으므로 아무 작업도하지 않고 종료
        if os.path.exists(os.path.join(self.ads2_folder, self.toolid)):
            self.logger.info(f"{self.toolid}のFCS処理が完結してないため処理を中止します")
            return D_SUCCESS

        # rem 6300装置のみzip圧縮しておく
        # 6300 장치 전용 zip 압축
        if self.modelid == 1:
            rtn = gz_compress(self.logger, self.reg_folder)
            if rtn != D_SUCCESS:
                self.logger.error(9001, "gzip fail")

        # rem 圧縮後の一覧表示
        # 압축 후 나열
        list_dir = os.listdir(self.reg_folder)
        for filename in list_dir:
            self.logger.info(f"reg_folder file = {filename}")

        # rem ログを受渡しフォルダ先にコピーする
        # 로그를 전달하고 폴더 대상에 복사
        shutil.move(self.reg_folder, self.ads2_folder)

        self.logger.info(f"{self.toolid} MoveToADS2_Tool Finished!!")
