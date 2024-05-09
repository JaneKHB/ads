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

import config.app_config as config
import util.time_util as time_util

from pathlib import Path
from sys import platform

from service.capa.capa_service import check_capacity
from service.ini.ini_service import get_ini_value
from service.remote.remote_service import isExistWget
from service.remote.request import subprocess_run
from service.remote.ssh_manager import SSHManager
from service.security.security_service import security_info
from service.common.common_service import file_size_logging, get_csv_info, rmtree
from service.zip.sevenzip_service import unzip, isExist7zip


class CollectFileDownload:
    def __init__(self, logger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.download_log = Path(config.FILE_LOG_LIPLUS_PATH, "downloadResult.log")

        self.current_dir = config.LIPLUS_DOWNLOAD_CURRENT_DIR
        self.tool_df = get_csv_info("LIPLUS", "DOWNLOAD")
        self.log_transfer = "file_transfer.log"
        self.timeout_second = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_ESP_HTTP_TIME_OUT"))

        self.espaddr = None  # 接続先ESPアドレス (ESP Address)
        self.userid = None  # ログインユーザ (User Id)
        self.userpasswd = None  # ログインユーザパスワード (User Password)
        self.local_fab = None  # LocalFab名 (置換前)
        self.remote_fab = None  # RemoteFab名 (置換後)

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
        # Capacity Check
        if not check_capacity("CollectFileDownload"):
            return

        # Processing Start Time
        processing_start_time = time.time()

        for _, elem in self.tool_df.iterrows():
            # rem --------------------------------------------------------------
            # rem  1:%%i : 接続先ESPアドレス (ESP Address)
            # rem  2:%%j : ログインユーザID (User Id)
            # rem  3:%%k : ログインユーザパスワード (User Password)
            # rem  4:%%l : LocalFab名（置換前）
            # rem  5:%%m : RemoteFab名（置換後）
            # rem --------------------------------------------------------------

            self._liplus_get_tool(elem.get('espaddr'), elem.get('userid'), elem.get('userpasswd'), elem.get('localfab'), elem.get('remotefab'))

        # Processing End Time
        processing_end_time = time.time()
        processing_time = processing_end_time - processing_start_time

        # Processing Time logging
        self.logger.info(f"Total time for the collection process:{processing_time :.2f}[sec] ")

    def _liplus_get_tool(self, espaddr, userid, userpasswd, local_fab, remote_fab):
        self.espaddr = espaddr
        self.userid = userid
        self.userpasswd = userpasswd
        self.local_fab = local_fab
        self.remote_fab = remote_fab

        protocol = "http"

        self.logger.info("liplus_get_tool start!!")

        # Make folder
        os.makedirs(self.reg_folder.absolute(), exist_ok=True)
        os.makedirs(self.zip_backup_folder.absolute(), exist_ok=True)

        # Check wget
        if isExistWget(self.logger) != 0:
            return

        # Check 7zip
        if isExist7zip(self.logger) != 0:
            return

        # Check two Factor Auth
        rtn, self.twofactor = security_info(self.logger, self.espaddr, self.securityinfo_path, self.securitykey_path)
        if rtn == config.D_SUCCESS and len(self.twofactor):
            protocol = "https"
            self.timeout_second = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_ESP_HTTPS_TIME_OUT"))
        elif rtn != config.D_SUCCESS:
            return

        self.logger.info("download start.")

        url = f"{protocol}://{self.espaddr}/OnDemandAgent/Download?USER={self.userid}&PW={self.userpasswd}"
        self.logger.info(f"download url : {url}")

        self.result_file = Path(self.reg_folder.absolute(), "result.tmp")
        self.download_file = Path(self.reg_folder.absolute(), "tmp_download.zip")

        # if file(result.tmp, tmp_download.zip) already exist, remove file.
        self.result_file.unlink(missing_ok=True)
        self.download_file.unlink(missing_ok=True)

        # khb. FIXME. subprocess wget request 시, cmd 로 Array 를 사용하면 동작 에러 발생(원인 파악 X. 리턴코드 = 1 or 3 or 4..)
        # khb. FIXME. 해당 기능(wget) 에 대해서는 Array 가 아닌 String 으로 처리한다.
        # download_command = [
        #     "wget"
        #     , url
        #     , "-d"
        #     , "-o"
        #     , str(self.result_file.absolute())
        #     , "-O"
        #     , str(self.download_file.absolute())
        #     , "-c"
        #     , "-t"
        #     , "1"
        #     , "-T"
        #     , str(self.timeout_second)
        #     # , self.twofactor
        # ]
        download_command = f'wget "{url}" -d -o {str(self.result_file.absolute())} -O {str(self.download_file.absolute())} -c -t 1 -T {str(self.timeout_second)}'
        print(download_command)

        # ** Use wget "subprocess" to find file-name in "result.tmp".
        # if it is an abnormal URL, "result.tmp", "tmp_download.zip" is created. "tmp_downlozd.zip" is blank file.
        # khb. todo. "result.tmp" 는 파일 이름(ESP 에서 제공하는 실제 파일 이름)을 획득하기 위해 사용되는것으로 판단됨. request 모듈로도 가능한지 체크 필요.
        self.logger.info(f"wget download command : {download_command}")
        download_ret = subprocess_run(self.logger, download_command)

        # set collect_file_name (==> find real file name in "result.tmp")
        collect_file_name = self._get_collect_file_name()

        if collect_file_name == "":
            self.logger.info("No collection required.")

            # remove result.tmp, download file
            self.result_file.unlink(missing_ok=True)
            self.download_file.unlink(missing_ok=True)

            self._end_wget()
            self._unzip()
            return

        # rename. tmp_download.zip ==> ESP download file name
        self.download_file.rename(Path(self.reg_folder.absolute(), collect_file_name))
        self.logger.info(f"rename [{self.download_file.absolute()}] -> [{collect_file_name}]")

        # check wget return code
        for _ in range(self.retry_max):
            if download_ret == 0:  # download success
                self.logger.info("wget File Download Request command success")
                self._response_check(self.result_file.absolute())

                # delete result.tmp
                self.result_file.unlink(missing_ok=True)
                self.logger.info(f"delete [{self.result_file.absolute()}]")

                # call upload_ok
                self._upload_ok(url, Path(self.reg_folder.absolute(), collect_file_name))
                self._end_wget()
                self._unzip()
                return
            else:
                # retry wget
                self.logger.info("wget retry start")
                self.logger.info(f"timeout {self.retry_sleep}")

                time.sleep(self.retry_sleep)
                download_ret = subprocess_run(self.logger, download_command)

                collect_file_name = self._get_collect_file_name()
                self.download_file.rename(Path(self.reg_folder.absolute(), collect_file_name))

                self.logger.warn("WARNING msg:Executed retry of file collection from ESP.")
                self.logger.info("wget retry end")

        # if download fail after retry, process ends
        if download_ret != 0:
            self.logger.error(f"[adslog] ERROR errorcode:2000 msg:Failed to retry collecting {collect_file_name} from ESP.")
            self._response_check(self.result_file.absolute(), is_error=True)

            # remove result.tmp, download file
            self.result_file.unlink(missing_ok=True)
            self.download_file.unlink(missing_ok=True)

            self._end_wget()
            self._unzip()
            return

        # call upload_ok
        self._upload_ok(url, Path(self.reg_folder.absolute(), collect_file_name))
        self._end_wget()
        self._unzip()

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

    def _unzip(self):
        # ZIP file unzip
        for f in self.reg_folder.iterdir():
            if f.suffix == ".zip":
                zip_fullpath = f.absolute()
                zip_filename = f.name.removesuffix(".zip")

                # Separate ZIP file names with "#" as delimiter
                tokens = zip_filename.split("#")
                fab_name = tokens[0]
                tool_num = tokens[1]
                remote_liplus_ip = tokens[2]

                if self.local_fab == fab_name:
                    fab_name = self.remote_fab

                remote_liplus_dir = f"/liplus/original_data/{fab_name}/{tool_num}"

                # ssh target folder check
                ssh_client = SSHManager(self.logger)
                ssh_client.create_ssh_client(ip=remote_liplus_ip, username=self.ldb_user, sshkey_path=self.sshkey_path)
                is_exist_target_folder = ssh_client.sftp_exists(remote_path=remote_liplus_dir)

                # unzip
                if is_exist_target_folder:
                    unzip_dir = Path(self.reg_folder.absolute(), zip_filename)

                    # Unzip File
                    unzip_start_time = time.time()
                    unzip_cmd = ["7z", "x", "-aoa", f"-o{unzip_dir.absolute()}", str(zip_fullpath)]
                    # khb. FIXME. 7zip 명령어(array)를 linux 에서 사용 시, 압축이 풀리지 않는 현상 발생(x 옵션이 아닌 -h 옵션이 적용되는것같음)
                    # khb. FIXME. 해당 기능(7zz x -aoa ...) 에 대해서는 Array 가 아닌 String 으로 처리한다.
                    if "linux" in platform:
                        unzip_cmd[0] = '7zz'
                        unzip_cmd = " ".join(unzip_cmd)

                    unzip_ret = unzip(self.logger, unzip_cmd)

                    # Unzipping time
                    unzip_end_time = time.time()
                    unzip_time = unzip_end_time - unzip_start_time
                    self.logger.info(f"Unzipping time of a [{f}]:{unzip_time:.3f}[sec]")

                    # if target_folder
                    # REM 압축 해제의 성공 여부는 압축 해제 대상 파일의 유무로 판단한다.
                    unzip_cnt = sum(1 for cf in unzip_dir.iterdir())
                    self.logger.info(f"Expanded file count:{unzip_cnt}")

                    if unzip_cnt > 0:
                        # REM *** ZIPファイルの解凍成功時
                        # REM *** ZIP 파일의 압축 해제 성공 시
                        # REM *** 解凍したZIPファイル内のファイルをLiplusDBへ転送する
                        # REM *** 압축을 푼 ZIP 파일의 파일을 LiplusDB로 전송
                        self.logger.info(f"[{f}] :unzip success")
                        self.logger.info(f"file transfer starts.")

                        tick_scp_start = time.time()
                        try:
                            # scp transfer
                            ssh_client = SSHManager(self.logger)
                            ssh_client.create_ssh_client(ip=remote_liplus_ip, username=self.ldb_user, sshkey_path=self.sshkey_path)
                            ssh_client.send_all_file(local_folder=unzip_dir, remote_folder=remote_liplus_dir)
                            ssh_client.close()

                            # SCP Transfer Success
                            self.logger.info(f"[{f}] :transfer success")
                            self.logger.info(f"del [{f}]")

                            f.unlink(missing_ok=True)
                        except Exception as ex:
                            # SCP Transfer Fail
                            self.logger.info(f"[adslog] ERROR errorcode:3000 msg:SCP transfer of {f} failed. {ex}")

                        tick_scp_end = time.time() - tick_scp_start
                        self.logger.info(f"Transfer time to LiplusDB server:{tick_scp_end}[sec]")

                        self.logger.info(f"rmdir [{unzip_dir}]")
                        rmtree(unzip_dir.absolute())

                        self.logger.info("file transfer end.")
                    else:
                        # REM *** ZIPファイルの解凍失敗時はBackupフォルダへZIPファイルを移動する
                        # REM *** ZIP 파일의 압축을 풀지 못하면 Backup 폴더로 ZIP 파일을 이동합니다.
                        self.logger.info(f"[{f}] :unzip failure")
                        self.logger.info(f"move [{f}] -> {self.zip_backup_folder}")
                        try:
                            # shutil.move(os.path.join(self.reg_folder.absolute(), f.name),
                            #             os.path.join(self.zip_backup_folder, f.name))
                            shutil.move(f, os.path.join(self.zip_backup_folder, f.name))    # khb. todo. 동작하는지 확인 필요!
                        except Exception as e:
                            self.logger.error(e)

                        self.logger.info(f"rmdir {unzip_dir}")
                        rmtree(unzip_dir.absolute())
                else:
                    self.logger.warn(f"LDB_PATH not found. '{remote_liplus_dir}'")

        self.logger.info("Unzip File Finished.")
        self.logger.info("LiplusGet_Tool Finished.")

    def _upload_ok(self, url, res_path):

        # Logging downloaded files
        file_size_logging(self.logger, "down", res_path, Path(self.current_dir, self.log_transfer).absolute())

        # Call collection files NEXT url
        next_url = url + "&NEXT=true"
        self.logger.info(f"next url : {next_url}")

        result_path = Path(self.reg_folder.absolute(), "result.tmp")

        # khb. FIXME. subprocess wget request 시, cmd 로 Array 를 사용하면 동작 에러 발생(원인 파악 X. 리턴코드 = 1 or 3 or 4..)
        # khb. FIXME. 해당 기능(wget) 에 대해서는 Array 가 아닌 String 으로 처리한다.
        # download_next_command = [
        #     "wget"
        #     , "--spider"
        #     , next_url
        #     , "-d"
        #     , "-o"
        #     , result_path.absolute()
        #     , "-t"
        #     , "1"
        #     , "-T"
        #     , str(self.timeout_second)
        #     # , self.twofactor
        # ]
        download_next_command = f'wget --spider "{next_url}" -d -o {result_path.absolute()} -t 1 -T {str(self.timeout_second)}'

        self.logger.info(f"wget next command : {download_next_command}")
        download_ret = subprocess_run(self.logger, download_next_command)

        # REM *** wgetコマンドの結果を解析し、エラーならNEXT処理をリトライ*********************************************
        # *** wget 명령의 결과를 구문 분석하고 오류가 있으면 NEXT 처리를 재시도 ******************************** *************
        for _ in range(self.retry_max):
            if download_ret == 0:
                self.logger.info("wget Next Request command success.")
                self._response_check(result_path.absolute())
                break
            else:
                self.logger.info("wget retry start")
                self.logger.info(f"timeout {self.retry_sleep}")
                time.sleep(self.retry_sleep)

                download_ret = subprocess_run(self.logger, download_next_command)

                self.logger.info("WARNING msg:Executed retry of file deletion instruction to ESP.")
                self.logger.info("wget retry end")

        # NEXT処理をリトライしてもエラーの場合、エラーログを出力
        # NEXT 처리를 재 시도해도 오류가 발생하면 오류 로그 출력
        if download_ret != 0:
            self.logger.info("[adslog] ERROR errorcode:2001 msg:Failed to retry file deletion instruction to ESP.")
            # 失敗時のログ出力(ErroCode)
            # 실패시 로그 출력 (ErroCode)
            self._response_check(result_path.absolute(), is_error=True)

        # 一時ファイルを削除する
        # 임시 파일 삭제
        result_path.unlink(missing_ok=True)
        self.logger.info(f"delete[{result_path.absolute()}]")

    def _get_collect_file_name(self):

        comp_sharp = "%23"
        comp_plus = "%2B"
        collect_file_name = ""

        # shlee 정말 필요한 부분일지 생각해봐야함
        def decode_url_encoded_chars(line):
            line = line.replace(comp_plus, '+')
            line = line.replace(comp_sharp, '#')
            return line

        result_tmp_name = Path(f"tmp_result_{datetime.datetime.now().strftime(time_util.TIME_FORMAT_6)}.tmp")
        with open(self.result_file.absolute(), 'r', errors='ignore') as log_file, \
                open(result_tmp_name.absolute(), 'w', errors='ignore') as tmp_file:
            for line in log_file:
                decoded_line = decode_url_encoded_chars(line.strip())
                tmp_file.write(decoded_line + '\n')

        # filename=찾아서 뒤에 붙은 파일이름 가져옴.
        with open(result_tmp_name.absolute(), "r", errors='ignore') as tmp_file:
            for line in tmp_file:
                if "filename=" in line:
                    _, value = line.split("filename=")
                    collect_file_name = value.strip()
                    break
        result_tmp_name.unlink(missing_ok=True)

        return collect_file_name

    def _end_wget(self):
        self.logger.info("Download end.")
