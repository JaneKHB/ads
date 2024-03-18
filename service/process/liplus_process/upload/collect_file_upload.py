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
from typing import Union
import pandas as pd
import shutil
import random
import subprocess
import datetime
import uuid

import config.app_config as config
import util.time_util as time_util
import xml.etree.ElementTree as elemTree

from service.ini.ini_service import get_ini_value
from service.logger.db_logger_service import DbLogger
from service.redis.redis_service import get_redis_global_status
from service.security.security_service import security_info
from service.common.common_service import create_upfile_tmp, file_size_logging

# \ADS\CollectRequestFileUpload\Auto_Upload.bat
class CollectFileUpload:
    def __init__(self, logger: DbLogger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = config.LIPLUS_UPLOAD_CURRENT_DIR
        self.ondemand_dir = config.LIPLUS_ONDEMAND_DIR
        self.upload_dir = os.path.join(config.LIPLUS_ONDEMAND_DIR, "Upload")
        self.log_name = "uploadResult.log"
        self.tool_df = CollectFileUpload.get_upload_info(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_UPLOAD_INFO_SKIP_LINE"))

        self.retry_max = 5
        self.retry_sleep = 2

        self.securityinfo_path = config.SECURITYINFO_PATH
        self.securitykey_path = get_ini_value(config.config_ini, "SECURITY", "SECURITYKEY_PATH")
        self.twofactor = {}

    @staticmethod
    def get_upload_info(skiprows_str=None):
        file_path = config.LIPLUS_UPLOAD_INFO_CSV
        if skiprows_str is None:
            # shlee todo 스킵로우 확인할것
            skiprows = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_UPLOAD_INFO_SKIP_LINE"))
        else:
            skiprows = int(skiprows_str)
        tool_df = pd.read_csv(file_path, names=config.LIPLUS_UPLOAD_INFO_HEADER,
                              dtype=config.LIPLUS_UPLOAD_DATA_TYPE,
                              encoding='shift_jis',
                              skiprows=skiprows, sep=',', index_col=False)
        return tool_df

    def start(self):

        os.makedirs(self.upload_dir, exist_ok=True)

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
            for f in os.listdir(self.ondemand_dir):
                # get file extention
                if os.path.splitext(f)[1].lower() == '.xml':
                    # rem ファイル移動
                    # 파일이동
                    try:
                        shutil.move(os.path.join(self.ondemand_dir, f), os.path.join(self.upload_dir, f))
                        # shlee todo 로그
                        # \ADS\CollectRequestFileUpload\Auto_Upload.bat - 57
                        # echo !date! !time! Move success: %%F >> %CURRENT_DIR%%LOG_NAME%
                    except:
                        # rem 収集要求ファイルの移動に失敗しても収集要求ファイルは削除せず、次回アップロード時に再度移動を行う
                        # 수집 요청 파일을 이동하지 못해도 수집 요청 파일을 삭제하지 않고 다음에 업로드 할 때 다시 이동합니다.
                        # shlee todo 로그
                        # echo !date! !time! Move failure: %%F >> %CURRENT_DIR%%LOG_NAME%
                        pass

            for f in os.listdir(self.upload_dir):
                # rem 収集要求ファイル内のFab名抽出
                # 수집 요청 파일에서 Fab 이름 추출
                if os.path.splitext(f)[1].lower() == '.xml':
                    # rem 収集要求ファイル内のFab名抽出
                    # 수집 요청 파일에서 Fab 이름 추출
                    tree = elemTree.parse(os.path.join(self.upload_dir, f))
                    ReqFabName = tree.find('Fab').text

                    # rem UploadInfo.csvのリモートFab名 と 収集要求ファイルのFab名 が一致している場合
                    # rem 収集要求ファイルのFab名称をUploadInfo.csvのローカルFab名に置換する。
                    # UploadInfo.csv의 원격 Fab 이름이 수집 요청 파일의 Fab 이름과 일치하면,
                    # 수집 요청 파일의 Fab 이름을 UploadInfo.csv의 로컬 Fab 이름으로 바꿉니다.
                    if remotefab_name == ReqFabName:
                        with open(os.path.join(self.upload_dir, f), "r+") as f_rw:
                            line = f_rw.readlines()
                            line = list(map(lambda x: x.replace(ReqFabName, localfab_name), line))
                            f_rw.truncate(0)
                            f_rw.seek(0)
                            f_rw.write(''.join(line))

                self._upload_tool(elem.get('espaddr'), elem.get('userid'), elem.get('userpasswd'), f)

    # \ADS\CollectRequestFileUpload\Upload_Tool.bat
    def _upload_tool(self, espaddr, userid, userpw, file):

        result = 0
        log_transfer = os.path.join(self.current_dir, "file_transfer.log")

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
            time_second = int(get_ini_value(config.config_ini, "EEC", "EEC_ESP_HTTPS_TIME_OUT"))
        elif rtn != config.D_SUCCESS:
            return result

        file_tmp = create_upfile_tmp(file, boundary)
        header = f'--header="Content-Type: multipart/form-data; boundary={boundary}"'
        postfile = f'--post-file="{file_tmp}"'
        url = f"{protocol}://{espaddr}/OnDemandAgent/Upload?USER={userid}&PW={userpw}"

        result_file_path = f"./result_{uuid.uuid4()}.tmp"
        command = [
            "wget"
            , header
            , postfile
            , url
            , "-d"
            , "-o"
            , result_file_path
            , "-t"
            , "1"
            , "T"
            , str(timeout_second)
            , self.twofactor
        ]
        res = subprocess.run(command)

        for _ in range(self.retry_max):
            if res.returncode == 0:
                # shlee todo \ADS\OnDemandCollectDownload\Upload_Tool.bat - 179
                # ErroCode、UploadID 어떻게 가져오는걸까
                file_size_logging("up", file, log_transfer)
                os.remove(file_tmp)
                os.remove(result_file_path)
            else:
                time.sleep(self.retry_sleep)
                res = subprocess.run(command)
