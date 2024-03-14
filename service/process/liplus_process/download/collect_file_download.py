"""
=========================================================================================
 :mod:`collect_file_download` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import os
from typing import Union
import pandas as pd
import shutil
import time
import subprocess
import datetime
import uuid

import config.app_config as config
import util.time_util as time_util

from service.ini.ini_service import get_ini_value
from service.logger.db_logger_service import DbLogger
from service.redis.redis_service import get_redis_global_status
from service.security.security_service import security_info
from service.common.common_service import file_size_logging, check_capacity

# \ADS\OnDemandCollectDownload\collectFileDownload.bat
class CollectFileDownload:
    def __init__(self, logger: DbLogger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.log_name = "downloadResult.log"

        self.current_dir = config.LIPLUS_DOWNLOAD_CURRENT_DIR
        self.tool_df = CollectFileDownload.get_download_info(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_DOWNLOAD_INFO_SKIP_LINE"))
        self.storage_path = ""
        # shlee todo 설정파일로
        self.limit_per = 5
        self.log_transfer = "file_transfer.log"
        self.timeout_second = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_ESP_HTTP_TIME_OUT"))

        self.espaddr = None  # 接続先ESPアドレス ESP 주소
        self.userid = None  # ログインユーザID 사용자명
        self.userpasswd = None  # ログインユーザパスワード 비밀번호
        self.local_fab = None  # LocalFab名（置換前） LocalFab 이름(교체 전)
        self.remote_fab = None  # RemoteFab名（置換後） RemoteFab 이름(교체 후)

        self.retry_max = 5
        self.retry_sleep = 2
        self.ldb_user = "lpsuser"
        self.reg_folder = os.path.join(self.current_dir, "Download")
        self.zip_backup_folder = os.path.join(self.current_dir, "Backup")

        self.sshkey_path = get_ini_value(config.config_ini, "SECURITY", "SSHKEY_PATH")
        self.securityinfo_path = config.SECURITYINFO_PATH
        self.securitykey_path = get_ini_value(config.config_ini, "SECURITY", "SECURITYKEY_PATH")
        self.twofactor = {}

    @staticmethod
    def get_download_info(skiprows_str=None):
        file_path = config.LIPLUS_DOWNLOAD_INFO_CSV
        if skiprows_str is None:
            # shlee todo 스킵로우 확인할것
            skiprows = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_DOWNLOAD_INFO_SKIP_LINE"))
        else:
            skiprows = int(skiprows_str)
        tool_df = pd.read_csv(file_path, names=config.LIPLUS_DOWNLOAD_INFO_HEADER, dtype=config.LIPLUS_DOWNLOAD_DATA_TYPE,
                              encoding='shift_jis',
                              skiprows=skiprows, sep=',', index_col=False)
        return tool_df

    def start(self):

        # REM 空き容量チェック（対象ドライブと空き容量リミット％を設定）
        # 여유 용량 체크(대상 드라이브와 여유 용량 리미트%를 설정)
        if not check_capacity("CollectFileDownload"):
            return

        # shlee todo 프로세스 동작 시간 구해야함. 여기부터
        tick_download_start = time.time()
        for _, elem in self.tool_df.iterrows():
            # Mainが緊急終了状態 긴급 종료 상태
            if get_redis_global_status(config.D_REDIS_SHUTDOWN_KEY) == config.D_SHUTDOWN:
                break

            # rem --------------------------------------------------------------
            # rem  1:%%i : 接続先ESPアドレス ESP 주소
            # rem  2:%%j : ログインユーザID 사용자ID
            # rem  3:%%k : ログインユーザパスワード 사용자 비밀번호
            # rem  4:%%l : LocalFab名（置換前） LocalFab 이름(교체 전)
            # rem  5:%%m : RemoteFab名（置換後） RemoteFab 이름(교체 후)
            # rem --------------------------------------------------------------

            self._liplusget_tool(elem.get('espaddr'), elem.get('userid'), elem.get('userpasswd'), elem.get('local_fab'), elem.get('remote_fab'))
        # 여기까지 OnDemandCollectDownload/CollectFileDownload.bat - 52
        tick_download_end = time.time() - tick_download_start

    # \ADS\OnDemandCollectDownload\LiplusGet_Tool.bat
    def _liplusget_tool(self, espaddr, userid, userpasswd, local_fab, remote_fab):

        self.espaddr = espaddr
        self.userid = userid
        self.userpasswd = userpasswd
        self.local_fab = local_fab
        self.remote_fab = remote_fab

        protocol = "http"

        os.makedirs(self.reg_folder, exist_ok=True)
        os.makedirs(self.zip_backup_folder, exist_ok=True)

        # REM 2要素認証の利用有無を判別
        # 2요소 인증의 이용 유무를 판별
        rtn, self.twofactor = security_info(self.logger, self.espaddr, self.securityinfo_path, self.securitykey_path)
        if rtn == config.D_SUCCESS and len(self.twofactor):
            protocol = "https"
            self.timeout_second = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_ESP_HTTPS_TIME_OUT"))
        elif rtn != config.D_SUCCESS:
            return

        url = f"{protocol}://{self.espaddr}/OnDemandAgent/Download?USER={self.userid}&PW={self.userpasswd}"
        # 다른 프로세스에서도 result.tmp를 만들기 uuid로 구분
        time_now = datetime.datetime.now()
        self.result_file_path = f"./result_{uuid.uuid4()}.tmp"
        self.download_file_path = os.path.join(self.reg_folder, os.path.join(self.reg_folder, f"tmp_download_{uuid.uuid4()}.zip"))
        command = [
            "wget"
            , url
            , "-d"
            , "-o"
            , self.result_file_path
            , "-O"
            , self.download_file_path
            , "-c"
            , "-t"
            , "1"
            , "T"
            , str(self.timeout_second)
            , self.twofactor
        ]
        res = subprocess.run(command)

        # REM *** wgetコマンドの結果を解析(エラーならリトライ)*********************************************
        # *** wget 명령의 결과를 구문 분석 (오류라면 재시도) *************************************** ***********
        for _ in range(self.retry_max):

            res_path = self._get_collect_file_name(self.reg_folder)

            if res.returncode == 0: # 성공
                os.remove(self.result_file_path)
                self._upload_ok(url, res_path)
                self._unzip()
                break
            else:
                time.sleep(self.retry_sleep)
                res = subprocess.run(command)

        os.remove(self.result_file_path)
        os.remove(self.download_file_path)

    def _unzip(self):

        # REM *** ZIPファイルの解凍
        # REM *** ZIP 파일 압축 해제
        for f in os.listdir(self.reg_folder):
            if os.path.splitext(f)[1].lower() == ".zip":
                zip_fullpath = os.path.abspath(f)
                zip_filename = os.path.basename(f)

                # REM *** ZIPファイル名を#を区切り文字として区切る
                # REM *** ZIP 파일 이름을 #을 구분 기호로 구분
                # rem %%a:Fab名 %%b:装置シリアル名 %%c:リモートLiplusDBのIPアドレス %%d:日付
                fab_name, tool_num, remote_liplus_ip = zip_filename.split("#")

                if self.local_fab == fab_name:
                    # rem DownloadInfo.csvのローカルFab名 と ZIPファイルのFab名 が一致している場合、
                    # rem DownloadInfo.csv의 로컬 Fab 이름이 ZIP 파일의 Fab 이름과 일치하면,
                    # rem Fab名称をDownloadInfo.csvのリモートFab名に置換する。
                    # rem Fab 이름을 DownloadInfo.csv의 원격 Fab 이름으로 바꿉니다.
                    fab_name = self.remote_fab

                remote_liplus_dir = os.path.join("liplus", "original_data", fab_name, tool_num)

                # REM *** LiplusDBサーバ転送先フォルダの存在確認 *******************
                # REM *** LiplusDB 서버 대상 폴더의 존재 확인 *******************
                command = [
                    "ssh"
                    , "-i"
                    , self.sshkey_path
                    , f"{self.ldb_user}@{remote_liplus_ip}"
                    , f"test -d {remote_liplus_dir}"
                ]
                res = subprocess.run(command)

                # REM *** ZIPの解凍
                if res.returncode == 0:
                    unzip_dir = os.path.join(self.reg_folder, zip_filename)
                    tick_unzip_start = time.time()
                    command_7z = [
                        "7z"
                        , "x"
                        , "-aoa"
                        , f"-o{unzip_dir}"
                        , zip_fullpath
                    ]
                    subprocess.run(command_7z)
                    tick_unzip_end = time.time() - tick_unzip_start

                    # REM 解凍の成功可否は解凍先のファイルの有無で判断する。
                    # REM 압축 해제의 성공 여부는 압축 해제 대상 파일의 유무로 판단한다.
                    if len(os.listdir(unzip_dir)) > 0:
                        # REM *** ZIPファイルの解凍成功時
                        # REM *** ZIP 파일의 압축 해제 성공 시
                        # REM *** 解凍したZIPファイル内のファイルをLiplusDBへ転送する
                        # REM *** 압축을 푼 ZIP 파일의 파일을 LiplusDB로 전송
                        tick_scp_start = time.time()
                        command_scp = [
                            "scp"
                            , "-oStrictHostKeyChecking=no"
                            , "-i"
                            , self.sshkey_path
                            , os.listdir(unzip_dir)
                            , f"{self.ldb_user}@{remote_liplus_ip}:{remote_liplus_dir}"
                        ]
                        res_scp = subprocess.run(command_scp)
                        tick_scp_end = time.time() - tick_scp_start

                        if res_scp.returncode != 0:
                            # REM *** 転送成功時
                            # REM *** 전송 성공 시
                            # REM *** ZIPファイルと解凍したフォルダを削除
                            os.remove(zip_fullpath)
                        else:
                            # REM *** 転送失敗時
                            # REM *** 전송 실패 시
                            #
                            # shlee todo log
                            pass
                        # REM *** 解凍したフォルダを削除
                        # REM *** 압축을 푼 폴더 삭제
                        os.remove(unzip_dir)
                    else:
                        # REM *** ZIPファイルの解凍失敗時はBackupフォルダへZIPファイルを移動する
                        # REM *** ZIP 파일의 압축을 풀지 못하면 Backup 폴더로 ZIP 파일을 이동합니다.
                        shutil.move(os.path.join(self.reg_folder, f), os.path.join(self.zip_backup_folder, f))
                        os.remove(unzip_dir)
                else:
                    # shlee todo log
                    pass


    def _upload_ok(self, url, res_path):

        # REM ダウンロードしたファイルのサイズをログ出力する
        # 다운로드한 파일의 크기를 로깅
        file_size_logging("down", res_path, os.path.join(self.current_dir, self.log_transfer))

        # REM *** 定期収集ファイルNEXT処理 ***********************************
        # *** 정기 수집 파일 NEXT 처리 ***********************************
        # rem ファイルダウンロードパス(NEXT)を出力
        # rem 파일 다운로드 경로 (NEXT) 출력
        url_check = url + "&NEXT=true"
        result_path = f"./result_{uuid.uuid4()}.tmp"
        command = [
            "wget"
            , "--spider"
            , url_check
            , "-d"
            , "-o"
            , result_path
            , "-t"
            , "1"
            , "-T"
            , str(self.timeout_second)
            , self.twofactor
        ]
        res = subprocess.run(command)

        # REM *** wgetコマンドの結果を解析し、エラーならNEXT処理をリトライ*********************************************
        # *** wget 명령의 결과를 구문 분석하고 오류가 있으면 NEXT 처리를 재시도 ******************************** *************
        for _ in range(self.retry_max):

            if res.returncode == 0:
                # shlee todo \ADS\OnDemandCollectDownload\LiplusGet_Tool.bat - 217
                # ErroCode、UploadID 어떻게 가져오는걸까
                break
            else:
                res = subprocess.run(command)

        if res.returncode != 0:
            # shlee 로그
            pass

        for _ in range(self.retry_max):
            if os.path.exists(result_path):
                os.remove(result_path)
            else:
                break

    def _get_collect_file_name(self, rename_basepath):

        comp_sharp = "%23"
        comp_plus = "%2B"
        collect_file_name = ""

        # shlee 정말 필요한 부분일지 생각해봐야함
        def decode_url_encoded_chars(line):
            line = line.replace(comp_plus, '+')
            line = line.replace(comp_sharp, '#')
            return line

        result_tmp_name = f"tmp_result_{datetime.datetime.now().strftime(time_util.TIME_FORMAT_6)}.tmp"
        with open(self.result_file_path, 'r', encoding='cp949', errors='ignore') as log_file, \
                open(result_tmp_name, 'w', encoding='cp949', errors='ignore') as tmp_file:
            for line in log_file:
                decoded_line = decode_url_encoded_chars(line.strip())
                tmp_file.write(decoded_line + '\n')

        # filename=찾아서 뒤에 붙은 파일이름 가져옴.
        with open(result_tmp_name, "r") as tmp_file:
            for line in tmp_file:
                if "filename=" in line:
                    _, value = line.split("filename=")
                    collect_file_name = value.strip()
                    break
        os.remove(result_tmp_name)

        if collect_file_name == "":
            os.remove(self.result_file_path)
            os.remove(self.download_file_path)
            return

        if os.path.exists(self.download_file_path):
            rename_path = os.path.join(rename_basepath, collect_file_name)
            os.rename(self.download_file_path, rename_path)
            return rename_path

