"""
=========================================================================================
 :mod:`auto_upload` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import datetime
import os
from typing import Union
import pandas as pd
import shutil
import random

import config.app_config as config
import service.remote.request as req
import util.time_util as time_util

from service.ini.ini_service import get_ini_value
from service.logger.db_logger_service import DbLogger
from service.redis.redis_service import get_redis_global_status
from service.security.security_service import security_info
from service.common.common_service import create_ulfile_tmp

# \ADS\UploadBatch\Auto_Upload.bat
class FdtFileUpload:
    def __init__(self, logger: DbLogger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = config.FDT_UP_CURRENT_DIR
        self.up_dir = config.FDT_UP_DIR
        self.tool_df = FdtFileUpload.get_uptool_info(get_ini_value(config.config_ini, "EEC", "EEC_UPTOOL_INFO_SKIP_LINE"))

        self.espaddr = None  # ESPアドレス ESP 주소
        self.userid = None  # ユーザ名 사용자명
        self.userpasswd = None  # パスワード 비밀번호
        self.toolid = None  # 装置名 장치명
        self.categoryID = None # カテゴリID 카테고리ID

        self.retry_max = 1
        self.retry_sleep = 10

        self.securityinfo_path = config.SECURITYINFO_PATH
        self.securitykey_path = get_ini_value(config.config_ini, "SECURITY", "SECURITYKEY_PATH")
        self.twofactor = {}

    @staticmethod
    def get_uptool_info(skiprows_str = None):
        file_path = config.FDT_UPTOOL_CSV
        if skiprows_str is None:
            # shlee todo 스킵로우 확인할것
            skiprows = int(get_ini_value(config.config_ini, "EEC", "EEC_UPTOOL_INFO_SKIP_LINE"))
        else:
            skiprows = int(skiprows_str)
        tool_df = pd.read_csv(file_path, names=config.FDT_UPTOOL_INFO_HEADER, dtype=config.FDT_UPTOOL_DATA_TYPE, encoding='shift_jis',
                              skiprows=skiprows, sep=',', index_col=False)
        return tool_df

    def start(self):

        os.makedirs(os.path.join(self.current_dir, "logs"), exist_ok=True)
        os.makedirs(os.path.join(self.current_dir, "UpFileBak"), exist_ok=True)

        for _, elem in self.tool_df.iterrows():
            # Mainが緊急終了状態 긴급 종료 상태
            if get_redis_global_status(config.D_REDIS_SHUTDOWN_KEY) == config.D_SHUTDOWN:
                break

            # rem --------------------------------------------------------------
            # rem  1:%%i : ESPアドレス ESP주소
            # rem  2:%%j : ユーザ名 사용자명
            # rem  3:%%k : パスワード 비밀번호
            # rem  4:%%l : 装置名 장치명
            # rem  5:%%m : カテゴリID 카테고리ID
            # rem --------------------------------------------------------------

            self.espaddr = elem.get('espaddr')
            self.userid = elem.get('userid')
            self.userpasswd = elem.get('userpasswd')
            self.toolid = elem.get('toolid')
            self.categoryID = elem.get('categoryid')

            # rem 拡張子「.tmp」はファイル転送中のものなのでそれ以外のファイルをターゲットとする
            # 확장자 ".tmp"는 파일 전송 중이므로 다른 파일을 대상으로합니다.
            for f in os.listdir(os.path.join(self.up_dir, self.toolid, self.categoryID)):
                if os.path.splitext(f)[1].lower() != '.tmp':
                    # rem この%%Fが拡張子.tmp以外のアップロードファイルのフルパスになる
                    # 이 %% F가 .tmp 확장명이 아닌 업로드 파일의 전체 경로입니다.
                    if self._upload_tool(os.path.join(self.up_dir, self.toolid, self.categoryID, f)):
                        upfilebak_dir = os.path.join(self.current_dir, "UpFileBak", self.toolid, self.categoryID)
                        os.makedirs(upfilebak_dir, exist_ok=True)
                        shutil.move(os.path.join(self.up_dir, self.toolid, self.categoryID, f), upfilebak_dir + os.path.basename(f))
                    else:
                        # shlee todo 로그!! 로그파일 생성!!
                        pass

    # \ADS\UploadBatch\Upload_Tool.bat
    def _upload_tool(self, file_path):

        result = 0
        # REM *** ファイルの存在確認 *******************************************************
        # 파일 존재 확인
        if not os.path.exists(file_path):
            return result

        # 배치파일에선 공백으로 넘어옴
        sppath = ""

        # REM wget実行時に指定するログ出力先のフルパス
        # wget 실행시 지정하는 로그 출력처의 풀 패스
        log_option = os.path.join(self.current_dir, "logs", f"wget_{self.toolid}.log")
        # REM *** ログ出力先フォルダの存在確認 *******************************************************
        # 로그 출력 대상 폴더의 존재 확인
        os.makedirs(os.path.dirname(log_option), exist_ok=True)

        # REM アップロードしたファイルサイズを出力するログのフルパス
        # 업로드한 파일 크기를 출력하는 로그의 전체 경로
        log_transfer = os.path.join(self.current_dir, "logs", f"{self.toolid}_file_transfer.log")

        time_now = datetime.datetime.now()
        # REM boundaryを生成
        # set BOUNDARY=%random%%custDate%%random%%custTime%%random%
        # shlee 바이트 제한이 있으려나...일단 걍 랜덤..batchfile %random% 범위만큼 랜덤
        boundary = f"{random.randrange(0, 32767 + 1)}{time_now.strftime(time_util.TIME_FORMAT_5)}{random.randrange(0, 32767 + 1)}" \
                   f"{time_now.strftime(time_util.TIME_FORMAT_6)[:-4]}{random.randrange(0, 32767 + 1)}"

        protocol = "http"
        time_second = int(get_ini_value(config.config_ini, "EEC", "EEC_ESP_HTTP_TIME_OUT"))

        # REM 2要素認証の利用有無を判別
        # 2요소 인증의 이용 유무를 판별
        rtn, self.twofactor = security_info(self.logger, self.espaddr, self.securityinfo_path, self.securitykey_path)
        if rtn == config.D_SUCCESS and len(self.twofactor):
            protocol = "https"
            time_second = int(get_ini_value(config.config_ini, "EEC", "EEC_ESP_HTTPS_TIME_OUT"))
        elif rtn != config.D_SUCCESS:
            return result

        url = f"{protocol}://{self.espaddr}/FileServiceCollectionAgent/Upload"
        param = f"?USER={self.userid}&PW={self.userpasswd}&TOOL={self.toolid}&KIND={self.categoryID}"
        if sppath != "":
            param += "&PATH=SPPATH"
            pass
        real_url = url + param
        header = {"Content-Type" : "multipart/form-data", "boundary" : boundary}

        # REM *** wgetコマンドで送信するファイルにboundaryを設定する ***********************
        # wget 명령으로 전송할 파일에 boundary 설정
        file_tmp = create_ulfile_tmp(file_path, boundary)
        rtn = req.esp_upload(self.logger, real_url, header, file_tmp, self.fname, time_second, self.twofactor
                             , self.retry_max, self.retry_sleep)
        file_tmp.unlink(missing_ok=True)


        '''
        # *** wgetコマンドの実行結果をログに出力する ***********************************
        # wget 명령의 실행 결과를 로그에 출력
        if exist %LOGOPTION% (
            copy %LOGOPTION%+result.tmp %LOGOPTION%
        ) else (
            copy result.tmp %LOGOPTION%
        )
        '''

        if rtn == config.D_SUCCESS:
            result = 1
            # shlee todo 로그남기기 - 수행된전송작업(up), 파일이름
            # log_transfer 없을경우 up/down,filename,filesize(MB) 헤더 쓰기
            # file(upload) 존재할경우
            # action(up),filename,filesize 쓰기
            # os.path.getsize(f) - 바이트단위임./1024/1024
            # custDate

        else:
            # shlee todo 에러 로그 남기기
            pass

        return result



