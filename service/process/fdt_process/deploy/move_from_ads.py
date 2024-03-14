"""
=========================================================================================
 :mod:`move_from_ads` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import os

from config.app_config import config_ini, FDT_CURRENT_DIR, D_SHUTDOWN, D_SUCCESS, FDT_ADS2_FOLDER, FDT_ADS2_UPLOAD, D_REDIS_SHUTDOWN_KEY
from service.common.common_service import xcopy_file_to_dir, rmdir_func
from service.gz.gz_service import gz_uncompress
from service.ini.ini_service import get_ini_value
from service.logger.db_logger_service import DbLogger
from service.process.fdt_process.download.file_download import FdtFileDownload
from service.redis.redis_service import get_redis_global_status


class FdtMoveFromAds:
    def __init__(self, logger: DbLogger, pname, sname, pno: int):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = FDT_CURRENT_DIR
        self.ads2_folder = FDT_ADS2_FOLDER  # "C:\\ADS\\LOG\\temp"
        self.ads2_upload = FDT_ADS2_UPLOAD  # "C:\\ADS\\LOG\\Upload"
        self.tool_df = FdtFileDownload.get_tool_info(get_ini_value(config_ini, "EEC", "EEC_TOOL_INFO_COM_ERR_SKIP_LINE"))

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
            # 	call %CURRENT_DIR%script\MoveFromADS_Tool.bat %%i %ADS2_UPLOAD%\%%i %CURRENT_DIR% %ADS2_FOLDER%

            self.move_from_ads_tool(elem.get('toolid'), f"{self.ads2_upload}{os.sep}{elem.get('toolid')}")

    def move_from_ads_tool(self, toolid, reg_folder):
        """
        ファイルダウンロードする子スクリプト

        :return: None
        """
        self.toolid = toolid  # 装置名
        self.reg_folder = reg_folder  # "C:\\ADS\\LOG\\Upload\装置名"

        # rem 受け渡しフォルダに装置名フォルダがない場合は、まだダウンロードされてない
        # 배달 폴더에 장치 이름 폴더가 없으면 아직 다운로드되지 않았습니다.
        # rem ということで処理を終了させる。
        # 따라서 처리를 종료합니다.
        if not os.path.exists(f"{self.ads2_folder}{os.sep}{self.toolid}"):
            self.logger.info("ダウンロード対象がないため処理を終了します")
            return

        # rem *** 排他対応 *********
        # rem 受け渡しフォルダから正規フォルダに移動させる。失敗した場合はコピー中
        # 배달 폴더에서 일반 폴더로 이동합니다. 실패하면 복사 중
        # rem ということで処理を終了させる
        # 그래서 처리를 종료
        try:
            os.rename(f"{self.ads2_folder}{os.sep}{self.toolid}", f"{self.ads2_folder}{os.sep}{self.toolid}_moved")
        except Exception as e:
            # ここはエラーではない。！！！
            # 여기는 오류가 아닙니다!!!
            self.logger.info("ADSからのコピー最中であるため処理を中止します")
            return

        # rem ログをコピーする
        # 로그 복사
        # call :execute xcopy %ADS2_FOLDER%\%TOOLID%_moved\* %REG_FOLDER%\ /R /Y
        source_folder = f"{self.ads2_folder}/{self.toolid}_moved"
        destination_folder = self.reg_folder
        os.makedirs(destination_folder, exist_ok=True)
        rtn = xcopy_file_to_dir(self.logger, source_folder, destination_folder)
        if rtn != D_SUCCESS:
            self.logger.error(9001, "ログコピーに失敗しました。処理を中止します")
            return

        # rem gzip圧縮されているログを解凍する
        # gzip 압축된 로그 압축 해제
        # rem call :execute gzip -d %REG_FOLDER%\*
        rtn = gz_uncompress(self.logger, self.reg_folder, is_src_delete=True)
        if rtn != D_SUCCESS:
            self.logger.error(9001, "gzip fail")

        # rem 解凍後のファイル一覧
        # 합축 해제 후 파일 목록
        list_dir = os.listdir(self.reg_folder)
        for filename in list_dir:
            self.logger.info(f"reg_folder file = {filename}")

        # rem 受け渡しリネーム済みフォルダをファイルごと削除する。
        # 전달된 이름이 지정된 폴더를 파일별로 삭제합니다.
        # call :execute rmdir /S /Q %ADS2_FOLDER%\%TOOLID%_moved
        rtn = rmdir_func(self.logger, f"{self.ads2_folder}{os.sep}{self.toolid}_moved")
        if rtn != D_SUCCESS:
            self.logger.error(9001, "rmdir_func fail")

        self.logger.info(":echod MoveFromADS_Tool Finished!!")



if __name__ == '__main__':
    logger = DbLogger("FDT", "DEPLOY", 0)
    obj = FdtMoveFromAds(logger, "FDT", "DEPLOY", 0)
    obj.start()