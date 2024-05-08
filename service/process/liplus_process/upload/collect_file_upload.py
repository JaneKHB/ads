"""
=========================================================================================
 :mod:`collect_file_upload` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import os
import subprocess
import time
import shutil
import random
import datetime
import xml.etree.ElementTree as elemTree

import config.app_config as config
import util.time_util as time_util

from typing import Union
from pathlib import Path

from service.ini.ini_service import get_ini_value
from service.remote.remote_service import isExistWget
from service.remote.request import request_subprocess, esp_upload
from service.security.security_service import security_info
from service.common.common_service import create_ulfile_tmp, file_size_logging, get_csv_info


class CollectFileUpload:
    def __init__(self, logger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = Path(config.LIPLUS_UPLOAD_CURRENT_DIR)
        self.ondemand_dir = Path(config.LIPLUS_ONDEMAND_DIR)
        self.upload_dir = Path(config.LIPLUS_UPLOAD_CURRENT_DIR, "Upload")
        self.log_name = "uploadResult.log"
        self.log_transfer = "file_transfer.log"
        self.timeout_second = int(get_ini_value(config.config_ini, "EEC", "LIPLUS_ESP_TIME_OUT"))

        self.tool_df = get_csv_info("LIPLUS", "UPLOAD")

        self.retry_max = int(get_ini_value(config.config_ini, "EEC", "DOWNLOAD_RETRY_CNT"))
        self.retry_sleep = 2

        self.securityinfo_path = config.SECURITYINFO_PATH
        self.securitykey_path = get_ini_value(config.config_ini, "SECURITY", "SECURITYKEY_PATH")
        self.twofactor = {}

    def start(self):
        self.upload_dir.mkdir(exist_ok=True)

        for _, elem in self.tool_df.iterrows():
            # Mainが緊急終了状態 긴급 종료 상태

            # rem --------------------------------------------------------------
            # rem 設定ファイル「UploadInfo.csv」では以下の項目が列挙されており、
            # rem 一行ずつ読み込んで、必要項目を取得する
            # rem --------------------------------------------------------------
            # rem  1:%%i : 接続先ESPのIPアドレス (ESP Address)
            # rem  2:%%j : ユーザ名 (User Id)
            # rem  3:%%k : パスワード (User Password)
            # rem  4:%%l : LocalFab名 (置換前)
            # rem  5:%%m : RemoteFab名 (置換後)
            # rem --------------------------------------------------------------

            localfab_name = elem.get('localfab')
            remotefab_name = str(elem.get('remotefab')).replace(' ', '')

            # XML File move
            for f in self.ondemand_dir.iterdir():
                if f.suffix == '.xml':
                    try:
                        shutil.move(f, os.path.join(self.upload_dir.absolute(), f.name))
                        self.logger.info(f"Move success: [{f}]")
                    except Exception as e:
                        # if the move fails, file not deleted and is moved at the next upload time.
                        self.logger.info(f"Move failure: [{f}]")
                        self.logger.error(e)

            for f in self.upload_dir.iterdir():
                if f.suffix == '.xml':
                    # get Fab name from Collection Request File(XML)
                    tree = elemTree.parse(f.absolute())
                    ReqFabName = tree.find('Fab').text

                    # If remote Fab name in UploadInfo.csv and the Fab name in XML match,
                    # Replace the Fab names in XML with the local Fab names in UploadInfo.csv.
                    if remotefab_name == ReqFabName:
                        with open(f.absolute(), "r+") as f_rw:
                            line = f_rw.readlines()
                            line = list(map(lambda x: x.replace(ReqFabName, localfab_name), line))
                            f_rw.truncate(0)
                            f_rw.seek(0)
                            f_rw.write(''.join(line))

                    upload_result = self._upload_tool(elem.get('espaddr'), elem.get('userid'), elem.get('userpasswd'), f.absolute())

                    if upload_result == 0:
                        # if upload success, remove file.
                        self.logger.info(f"delete [{f}]")
                        f.unlink()
                    else:
                        # if upload fails, file is not deleted and upload at the next upload time.
                        self.logger.info(f"ERROR:!ERRORLEVEL! Upload failure:{f}")

    # ADS\CollectRequestFileUpload\Upload_Tool.bat
    def _upload_tool(self, espaddr, userid, userpw, file_path):
        result = 0
        protocol = "http"

        self.logger.info("upload_tool start!!")

        ulfile = Path(file_path)
        if not ulfile.exists():
            self.logger.info(f"upload file does not exist")
            return result

        # Check wget
        if isExistWget(self.logger) != 0:
            return 99

        # Check two Factor Auth
        rtn, self.twofactor = security_info(self.logger, espaddr, self.securityinfo_path, self.securitykey_path)
        if rtn == config.D_SUCCESS and len(self.twofactor):
            protocol = "https"
            # self.timeout_second = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_ESP_HTTPS_TIME_OUT"))
        elif rtn != config.D_SUCCESS:
            return result

        time_now = datetime.datetime.now()
        # boundary create
        # set BOUNDARY=%random%%custDate%%random%%custTime%%random%
        boundary = f"{random.randrange(0, 32767 + 1)}{time_now.strftime(time_util.TIME_FORMAT_5)}{random.randrange(0, 32767 + 1)}" \
                   f"{time_now.strftime(time_util.TIME_FORMAT_6)[:-4]}{random.randrange(0, 32767 + 1)}"

        file_tmp = create_ulfile_tmp(ulfile.absolute(), boundary)

        url = f"{protocol}://{espaddr}/OnDemandAgent/Upload?USER={userid}&PW={userpw}"
        self.logger.info(f"upload url : {url}")

        result_file = Path(self.upload_dir.absolute(), "result.tmp")

        # khb. FIXME. subprocess wget post multipart request 시, cmd 로 Array 를 사용하면 동작 에러 발생(원인 파악 X. 리턴코드 = 1 or 3 or 4..)
        # khb. FIXME. 해당 기능(wget, post, multipart) 에 대해서는 Array 가 아닌 String 으로 처리한다.
        # upload_command = [
        #     "wget"
        #     , header
        #     , postfile
        #     , url
        #     , "-d"
        #     , "-o"
        #     , str(result_file.absolute())
        #     , "-t"
        #     , "1"
        #     , "-T"
        #     , str(self.timeout_second)
        #     # , self.twofactor
        # ]

        if config.IS_USE_WGET:
            header = f'--header="Content-Type: multipart/form-data; boundary={boundary}"'
            postfile = f'--post-file="{str(file_tmp.absolute())}"'

            # shlee todo twofactor
            upload_command = f'wget {header} {postfile} {url} -d -o {result_file.absolute()} -t 1 -T {self.timeout_second}'
            self.logger.info(f"wget upload command : {upload_command}")
            upload_ret = request_subprocess(self.logger, upload_command, self.retry_max, self.retry_sleep)
        else:
            header = {'Content-Type' : 'multipart/form-data',
                      'boundary' : boundary}
            postfile = {'file' : open(file_tmp.absolute(), "rb")}
            self.logger.info(f"reuest : headers:{header}, url:{url}, file:{postfile}")
            upload_ret = esp_upload(self.logger, url, header, postfile, self.timeout_second, self.twofactor, self.retry_max, self.retry_sleep)

        if upload_ret == config.D_SUCCESS:
            self.logger.info("wget upload command success.")
            file_size_logging(self.logger, "up", ulfile.absolute())
        else:
            self.logger.info(f"[adslog] ERROR errorcode:2002 msg:Failed to retry ondemand request for {ulfile.absolute()} to ESP.")
            result = upload_ret

        self._response_check(result_file.absolute(), is_error=False if upload_ret == config.D_SUCCESS else True)
        file_tmp.unlink(missing_ok=True)
        result_file.unlink(missing_ok=True)
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
