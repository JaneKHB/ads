"""
=========================================================================================
 :mod:`collect_file_upload` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import os
import time
import shutil
import random
import subprocess
import datetime
import uuid
import xml.etree.ElementTree as elemTree

import config.app_config as config
import util.time_util as time_util

from typing import Union
from pathlib import Path

from service.ini.ini_service import get_ini_value
from service.logger.db_logger_service import DbLogger
from service.redis.redis_service import get_redis_global_status
from service.security.security_service import security_info
from service.common.common_service import create_upfile_tmp, file_size_logging, get_csv_info

# \ADS\CollectRequestFileUpload\Auto_Upload.bat
class CollectFileUpload:
    def __init__(self, logger: DbLogger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = Path(config.LIPLUS_UPLOAD_CURRENT_DIR)
        self.ondemand_dir = Path(config.LIPLUS_ONDEMAND_DIR)
        self.upload_dir = Path(config.LIPLUS_ONDEMAND_DIR, "Upload")
        self.log_name = "uploadResult.log"
        self.tool_df = get_csv_info("LIPLUS", "UPLOAD")

        self.retry_max = 5
        self.retry_sleep = 2

        self.securityinfo_path = config.SECURITYINFO_PATH
        self.securitykey_path = get_ini_value(config.config_ini, "SECURITY", "SECURITYKEY_PATH")
        self.twofactor = {}

    def start(self):

        self.upload_dir.mkdir(exist_ok=True)

        for _, elem in self.tool_df.iterrows():
            # Mainが緊急終了状態 긴급 종료 상태
            if get_redis_global_status(config.D_REDIS_SHUTDOWN_KEY) == config.D_SHUTDOWN:
                break

            # rem --------------------------------------------------------------
            # rem 設定ファイル「UploadInfo.csv」では以下の項目が列挙されており、
            # rem 一行ずつ読み込んで、必要項目を取得する
            # rem --------------------------------------------------------------
            # rem  1:%%i : 接続先ESPのIPアドレス 연결대상 ESP의 IP주소
            # rem  2:%%j : ユーザ名 사용자명
            # rem  3:%%k : パスワード 비밀번호
            # rem  4:%%l : LocalFab名（置換前） LocalFab 이름(교체 전)
            # rem  5:%%m : RemoteFab名（置換後） RemoteFab 이름(교체 후)
            # rem --------------------------------------------------------------

            localfab_name = elem.get('local_fab')
            remotefab_name = str(elem.get('remote_fab')).replace(' ', '')

            # rem XMLファイルを対象とする
            # XML 파일을 대상으로
            for f in self.ondemand_dir.iterdir():
                # get file extention
                if f.suffix == '.xml':
                    # rem ファイル移動
                    # 파일이동
                    try:
                        shutil.move(f, os.path.join(self.upload_dir.absolute(), f.name))
                        self.logger.info(f"Move success: {f}")
                    except Exception as e:
                        # rem 収集要求ファイルの移動に失敗しても収集要求ファイルは削除せず、次回アップロード時に再度移動を行う
                        # 수집 요청 파일을 이동하지 못해도 수집 요청 파일을 삭제하지 않고 다음에 업로드 할 때 다시 이동합니다.
                        self.logger.info(f"Move failure: {f}")
                        self.logger.error(e)

            for f in self.upload_dir.iterdir():
                # rem 収集要求ファイル内のFab名抽出
                # 수집 요청 파일에서 Fab 이름 추출
                if f.suffix == '.xml':
                    # rem 収集要求ファイル内のFab名抽出
                    # 수집 요청 파일에서 Fab 이름 추출
                    tree = elemTree.parse(f.absolute())
                    ReqFabName = tree.find('Fab').text

                    # rem UploadInfo.csvのリモートFab名 と 収集要求ファイルのFab名 が一致している場合
                    # rem 収集要求ファイルのFab名称をUploadInfo.csvのローカルFab名に置換する。
                    # UploadInfo.csv의 원격 Fab 이름이 수집 요청 파일의 Fab 이름과 일치하면,
                    # 수집 요청 파일의 Fab 이름을 UploadInfo.csv의 로컬 Fab 이름으로 바꿉니다.
                    if remotefab_name == ReqFabName:
                        with open(f.absolute(), "r+") as f_rw:
                            line = f_rw.readlines()
                            line = list(map(lambda x: x.replace(ReqFabName, localfab_name), line))
                            f_rw.truncate(0)
                            f_rw.seek(0)
                            f_rw.write(''.join(line))

                    if self._upload_tool(elem.get('espaddr'), elem.get('userid'), elem.get('userpasswd'), f.absolute()) == 0:
                        # アップロードに成功した場合ファイルを削除する
                        # 업로드에 성공하면 파일 삭제
                        self.logger.info(f"delete {f}")
                        f.unlink()
                    else:
                        # アップロードに失敗
                        # 업로드 실패
                        # 収集要求ファイルのアップロードに失敗しても収集要求ファイルは削除せず、次回アップロード時に再度転送を行う
                        # 수집 요청 파일을 업로드하지 못해도 수집 요청 파일을 삭제하지 않고 다음에 업로드할 때 다시 전송합니다.
                        self.logger.info(f"ERROR:!ERRORLEVEL! Upload failure:{f}")


    # \ADS\CollectRequestFileUpload\Upload_Tool.bat
    def _upload_tool(self, espaddr, userid, userpw, file_path):

        result = 0

        ulfile = Path(file_path)
        log_transfer = Path(self.current_dir.absolute(), "file_transfer.log")

        if not ulfile.exists():
            self.logger.info(f"upload file does not exist")
            return result

        protocol = "http"
        timeout_second = int(get_ini_value(config.config_ini, "EEC", "EEC_ESP_HTTP_TIME_OUT"))

        time_now = datetime.datetime.now()
        # REM boundaryを生成
        # set BOUNDARY=%random%%custDate%%random%%custTime%%random%
        boundary = f"{random.randrange(0, 32767 + 1)}{time_now.strftime(time_util.TIME_FORMAT_5)}{random.randrange(0, 32767 + 1)}" \
                   f"{time_now.strftime(time_util.TIME_FORMAT_6)[:-4]}{random.randrange(0, 32767 + 1)}"

        # REM 2要素認証の利用有無を判別
        # 2요소 인증의 이용 유무를 판별
        rtn, self.twofactor = security_info(self.logger, espaddr, self.securityinfo_path, self.securitykey_path)
        if rtn == config.D_SUCCESS and len(self.twofactor):
            protocol = "https"
            time_second = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_ESP_HTTPS_TIME_OUT"))
        elif rtn != config.D_SUCCESS:
            return result

        file_tmp = create_upfile_tmp(ulfile.absolute(), boundary)
        header = f'--header="Content-Type: multipart/form-data; boundary={boundary}"'
        postfile = f'--post-file="{str(file_tmp.absolute())}"'
        url = f"{protocol}://{espaddr}/OnDemandAgent/Upload?USER={userid}&PW={userpw}"

        result_file_path = Path(f"./result_{uuid.uuid4()}.tmp")
        command = [
            "wget"
            , header
            , postfile
            , url
            , "-d"
            , "-o"
            , result_file_path.absolute()
            , "-t"
            , "1"
            , "T"
            , str(timeout_second)
            , self.twofactor
        ]
        self.logger.info(f"subprocess run {command}")
        res = subprocess.run(command)

        for _ in range(self.retry_max):
            try:
                if res.returncode == 0:
                    self.logger.info("wget upload command success.")

                    self._response_check(result_file_path.absolute())
                    file_size_logging(self.logger, "up", ulfile.absolute(), log_transfer.absolute())

                    self.logger.info(f"delete {file_tmp.absolute()}")

                    file_tmp.unlink(missing_ok=True)
                    result_file_path.unlink(missing_ok=True)
                else:
                    self.logger.info("wget retry start")
                    self.logger.info(f"timeout {self.retry_sleep}")

                    time.sleep(self.retry_sleep)
                    res = subprocess.run(command)

                    self.logger.info("WARNING msg:Executed retry of ondemand request to ESP.")
                    self.logger.info("wget retry end")
            except Exception as e:
                self.logger.error(e)

        # リトライ時のWgetコマンドの結果を解析する
        # 재시도시 Wget 명령의 결과 분석
        if not res.returncode == 0:
            self.logger.info(f"[adslog] ERROR errorcode:2002 msg:Failed to retry ondemand request for {ulfile.absolute()} to ESP.")
            self._response_check(result_file_path.absolute(), is_error=True)
            result = res.returncode

        file_tmp.unlink(missing_ok=True)
        self.logger.info("Upload_Tool Finished")

        return result

    def _response_check(self, result_path, is_error=False):
        read_line = []
        with open(result_path, "r", errors="ignore") as f:
            read_line = f.read().splitlines()

        for line in read_line:
            if "ErrorCode:" in line:
                self.logger.info(line)
            if not is_error:
                if "UploadId:" in line:
                    self.logger.info(line)
                if "LiplusAPAddress:" in line:
                    self.logger.info(line)
                if "ToolSerialNo:" in line:
                    self.logger.info(line)
                if "FabName:" in line:
                    self.logger.info(line)
