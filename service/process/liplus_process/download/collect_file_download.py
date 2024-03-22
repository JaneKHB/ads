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
import shutil
import time
import subprocess
import datetime
import uuid

import config.app_config as config
import util.time_util as time_util

from pathlib import Path

from service.ini.ini_service import get_ini_value
from service.logger.db_logger_service import DbLogger
from service.redis.redis_service import get_redis_global_status
from service.security.security_service import security_info
from service.common.common_service import file_size_logging, check_capacity, get_csv_info, rmtree

# \ADS\OnDemandCollectDownload\collectFileDownload.bat
class CollectFileDownload:
    def __init__(self, logger: DbLogger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.download_log = Path(config.FILE_LOG_LIPLUS_PATH, "downloadResult.log")

        self.current_dir = config.LIPLUS_DOWNLOAD_CURRENT_DIR
        self.tool_df = get_csv_info("LIPLUS", "DOWNLOAD")
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
        self.reg_folder = Path(self.current_dir, "Download")
        self.zip_backup_folder = Path(self.current_dir, "Backup")

        self.sshkey_path = get_ini_value(config.config_ini, "SECURITY", "SSHKEY_PATH")
        self.securityinfo_path = config.SECURITYINFO_PATH
        self.securitykey_path = get_ini_value(config.config_ini, "SECURITY", "SECURITYKEY_PATH")
        self.twofactor = {}

    def start(self):

        # REM 空き容量チェック（対象ドライブと空き容量リミット％を設定）
        # 여유 용량 체크(대상 드라이브와 여유 용량 리미트%를 설정)
        if not check_capacity("CollectFileDownload"):
            return

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

        tick_download_end = time.time() - tick_download_start
        self.logger.info(f"Total time for the collection process:{tick_download_end}[sec]")

    # \ADS\OnDemandCollectDownload\LiplusGet_Tool.bat
    def _liplusget_tool(self, espaddr, userid, userpasswd, local_fab, remote_fab):

        self.espaddr = espaddr
        self.userid = userid
        self.userpasswd = userpasswd
        self.local_fab = local_fab
        self.remote_fab = remote_fab

        protocol = "http"

        self.logger.info("LiplusGet_Tool Start.")

        self.reg_folder.mkdir(exist_ok=True)
        self.zip_backup_folder.mkdir(exist_ok=True)

        # REM 2要素認証の利用有無を判別
        # 2요소 인증의 이용 유무를 판별
        rtn, self.twofactor = security_info(self.logger, self.espaddr, self.securityinfo_path, self.securitykey_path)
        if rtn == config.D_SUCCESS and len(self.twofactor):
            protocol = "https"
            self.timeout_second = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_ESP_HTTPS_TIME_OUT"))
        elif rtn != config.D_SUCCESS:
            return
        self.logger.info("download start.")
        url = f"{protocol}://{self.espaddr}/OnDemandAgent/Download?USER={self.userid}&PW={self.userpasswd}"
        # 다른 프로세스에서도 result.tmp를 만들기 uuid로 구분

        time_now = datetime.datetime.now()
        self.result_file = Path(f"./result_{uuid.uuid4()}.tmp")
        self.download_file = Path(self.reg_folder.absolute(), f"tmp_download_{uuid.uuid4()}.zip")
        command = [
            "wget"
            , url
            , "-d"
            , "-o"
            , self.result_file.absolute()
            , "-O"
            , self.download_file.absolute()
            , "-c"
            , "-t"
            , "1"
            , "T"
            , str(self.timeout_second)
            , self.twofactor
        ]
        self.logger.info(f"subprocess run {command}")
        res = subprocess.run(command)

        # REM *** wgetコマンドの結果を解析(エラーならリトライ)*********************************************
        # *** wget 명령의 결과를 구문 분석 (오류라면 재시도) *************************************** ***********
        for _ in range(self.retry_max):

            collect_file_name = self._get_collect_file_name(self.reg_folder.absolute())
            if collect_file_name == "":
                self.logger.info("No collection required.")
                break

            self.download_file.rename(collect_file_name)

            if res.returncode == 0: # 성공
                self.logger.info("wget File Download Request command success")

                self._response_check(self.result_file.absolute())
                self.result_file.unlink(missing_ok=True)
                self._upload_ok(url, collect_file_name)
                break
            else:
                self.logger.info("wget retry start")
                self.logger.info(f"timeout {self.retry_sleep}")

                time.sleep(self.retry_sleep)
                res = subprocess.run(command)

                self.logger.info("WARNING msg:Executed retry of file collection from ESP.")
                self.logger.info("wget retry end")

        # リトライしてもファイル取れなかったらダウンロード処理を終了する
        # 재시도해도 파일을 얻을 수 없으면 다운로드 처리를 종료합니다.
        if res.returncode != 0:
            self.logger.info(f"[adslog] ERROR errorcode:2000 msg:Failed to retry collecting {collect_file_name} from ESP.")
            self._response_check(self.result_file.absolute(), is_error=True)

        self.result_file.unlink(missing_ok=True)
        self.download_file.unlink(missing_ok=True)

        self.logger.info("Download end.")
        self.logger.info("UnZip File Start.")
        self._unzip()

    def _response_check(self, result_path, is_error = False):
        read_line = []
        with open(result_path, "r", errors="ignore") as f:
            read_line = f.read().splitlines()

        for line in read_line:
            if "ErrorCode:" in line:
                self.logger.info(line)
            if not is_error:
                if "UploadId:" in line:
                    self.logger.info(line)

    def _unzip(self):

        # REM *** ZIPファイルの解凍
        # REM *** ZIP 파일 압축 해제
        for f in self.reg_folder.iterdir():
            if f.suffix == ".zip":
                # zip_fullpath = f.absolute()
                zip_filename = f.name

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

                remote_liplus_dir = Path("liplus", "original_data", fab_name, tool_num)

                # REM *** LiplusDBサーバ転送先フォルダの存在確認 *******************
                # REM *** LiplusDB 서버 대상 폴더의 존재 확인 *******************
                command = [
                    "ssh"
                    , "-i"
                    , self.sshkey_path
                    , f"{self.ldb_user}@{remote_liplus_ip}"
                    , f"test -d {remote_liplus_dir.absolute()}"
                ]
                self.logger.info(f"subprocess run {command}")
                res = subprocess.run(command)

                # REM *** ZIPの解凍
                if res.returncode == 0:
                    unzip_dir = Path(self.reg_folder.absolute(), zip_filename)
                    tick_unzip_start = time.time()
                    command_7z = [
                        "7z"
                        , "x"
                        , "-aoa"
                        , f"-o{unzip_dir.absolute()}"
                        , f.absolute()
                    ]
                    self.logger.info(f"subprocess run {command_7z}")

                    subprocess.run(command_7z)
                    tick_unzip_end = time.time() - tick_unzip_start

                    self.logger.info(f"Unzipping time of a {f}:{tick_unzip_end}[sec]")

                    # REM 解凍の成功可否は解凍先のファイルの有無で判断する。
                    # REM 압축 해제의 성공 여부는 압축 해제 대상 파일의 유무로 판단한다.
                    unzip_cnt = sum(1 for cf in unzip_dir.iterdir())
                    self.logger.info(f"Expanded file count:{unzip_cnt}")
                    if unzip_cnt > 0:
                        # REM *** ZIPファイルの解凍成功時
                        # REM *** ZIP 파일의 압축 해제 성공 시
                        # REM *** 解凍したZIPファイル内のファイルをLiplusDBへ転送する
                        # REM *** 압축을 푼 ZIP 파일의 파일을 LiplusDB로 전송
                        self.logger.info(f"{f} :unzip success")
                        self.logger.info(f"file transfer starts.")
                        tick_scp_start = time.time()
                        command_scp = [
                            "scp"
                            , "-oStrictHostKeyChecking=no"
                            , "-i"
                            , self.sshkey_path
                            , [f for f in unzip_dir.iterdir()]
                            , f"{self.ldb_user}@{remote_liplus_ip}:{remote_liplus_dir.absolute()}"
                        ]
                        self.logger.info(f"subprocess run {command_scp}")
                        res_scp = subprocess.run(command_scp)
                        tick_scp_end = time.time() - tick_scp_start
                        self.logger.info(f"Transfer time to LiplusDB server:{tick_scp_end}[sec]")

                        if res_scp.returncode != 0:
                            # REM *** 転送成功時
                            # REM *** 전송 성공 시
                            # REM *** ZIPファイルと解凍したフォルダを削除
                            self.logger.info(f"{f} :transfer success")
                            self.logger.info(f"del {f}")
                            f.unlink(missing_ok=True)
                        else:
                            # REM *** 転送失敗時
                            # REM *** 전송 실패 시
                            self.logger.info(f"[adslog] ERROR errorcode:3000 msg:SCP transfer of {f} failed.")
                            pass
                        # REM *** 解凍したフォルダを削除
                        # REM *** 압축을 푼 폴더 삭제
                        self.logger.info(f"rmdir {unzip_dir}")
                        rmtree(unzip_dir.absolute())
                        self.logger.info("file transfer end.")
                    else:
                        # REM *** ZIPファイルの解凍失敗時はBackupフォルダへZIPファイルを移動する
                        # REM *** ZIP 파일의 압축을 풀지 못하면 Backup 폴더로 ZIP 파일을 이동합니다.
                        self.logger.info(f"{f} :unzip failure")
                        self.logger.info(f"move {f} -> {self.zip_backup_folder}")
                        shutil.move(os.path.join(self.reg_folder.absolute(), f), os.path.join(self.zip_backup_folder, f))
                        self.logger.info(f"rmdir {unzip_dir}")
                        rmtree(unzip_dir.absolute())
                else:
                    self.logger.info(f"!LDB_PATH! not found.")
        self.logger.info("Unzip File Finished.")
        self.logger.info("LiplusGet_Tool Finished.")

    def _upload_ok(self, url, res_path):

        # REM ダウンロードしたファイルのサイズをログ出力する
        # 다운로드한 파일의 크기를 로깅
        file_size_logging("down", res_path, Path(self.current_dir, self.log_transfer).absolute())

        # REM *** 定期収集ファイルNEXT処理 ***********************************
        # *** 정기 수집 파일 NEXT 처리 ***********************************
        # rem ファイルダウンロードパス(NEXT)を出力
        # rem 파일 다운로드 경로 (NEXT) 출력
        url_check = url + "&NEXT=true"
        result_path = Path(f"./result_{uuid.uuid4()}.tmp")
        command = [
            "wget"
            , "--spider"
            , url_check
            , "-d"
            , "-o"
            , result_path.absolute()
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
            if result_path.exists():
                result_path.unlink(missing_ok=True)
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

        result_tmp_name = Path(f"tmp_result_{datetime.datetime.now().strftime(time_util.TIME_FORMAT_6)}.tmp")
        with open(self.result_file.absolute(), 'r', encoding='cp949', errors='ignore') as log_file, \
                open(result_tmp_name.absolute(), 'w', encoding='cp949', errors='ignore') as tmp_file:
            for line in log_file:
                decoded_line = decode_url_encoded_chars(line.strip())
                tmp_file.write(decoded_line + '\n')

        # filename=찾아서 뒤에 붙은 파일이름 가져옴.
        with open(result_tmp_name.absolute(), "r") as tmp_file:
            for line in tmp_file:
                if "filename=" in line:
                    _, value = line.split("filename=")
                    collect_file_name = value.strip()
                    break
        result_tmp_name.unlink(missing_ok=True)

        if collect_file_name == "":
            self.result_file.unlink(missing_ok=True)
            self.download_file.unlink(missing_ok=True)
            return None

        if self.download_file.exists():
            rename_path = Path(rename_basepath, collect_file_name)
            self.download_file.rename(rename_path.absolute())
            return rename_path.absolute()

