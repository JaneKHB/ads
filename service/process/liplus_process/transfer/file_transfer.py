"""
=========================================================================================
 :mod:`file_transfer` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import os
import subprocess
import time
from typing import Union

from config.app_config import D_SUCCESS, D_ERROR, LIPLUS_CURRENT_DIR, LIPLUS_REG_FOLDER_DEFAULT, config_ini, \
    FILE_LOG_LIPLUS_TRANSFER_PATH
from service.capa.capa_service import check_capacity
from service.common.common_service import remove_files_in_folder, rmdir_func, get_csv_info
from service.ini.ini_service import get_ini_value
from service.process.liplus_process.get.file_get import LiplusFileGet
from service.remote.remote_service import remote_check_path_by_sshkey
from service.remote.ssh_manager import SSHManager
from service.sevenzip.sevenzip_service import unzip


class LiplusFileTransfer:
    def __init__(self, logger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = LIPLUS_CURRENT_DIR
        self.tool_df = get_csv_info("LIPLUS", "TRANSFER", self.pno)
        self.sshkey_path = get_ini_value(config_ini, "SECURITY", "SSHKEY_PATH")

        self.toolid = None  # 装置名 (MachineName)
        self.reg_folder = None  # 正規フォルダパス (* Liplus Data Download Folder)

    def start(self):
        # Capacity Check
        if not check_capacity("LiplusTransfer"):
            return

        # Processing Start Time
        processing_start_time = time.time()

        for _, elem in self.tool_df.iterrows():
            # 	rem	--------------------------------------------------------------
            # 	rem	設定ファイル「LiplusToolInfo.csv」から、
            # 	rem	一行ずつ読み込んで、必要項目を取得する
            # 	rem	--------------------------------------------------------------
            # 	rem	 2:%%i : 装置名
            # 	rem	 5:%%j : LiplusDBのIPアドレス\LiplusDBサーバのデータ転送先
            # 	rem	 8:%%k : ADSサーバー内の保存先パス
            # 	rem	--------------------------------------------------------------
            #
            # 	call %CURRENT_DIR%script\LiplusTransfer_Tool.bat %%i %%j "%%k" %CURRENT_DIR%

            self.liplus_transfer_tool(elem.get('toolid'), elem.get('ldb_dir'), elem.get('reg_folder'))

        # Processing End Time
        processing_end_time = time.time()
        processing_time = processing_end_time - processing_start_time

        # Processing Time logging
        logger_header = f"[{self.toolid}]"
        self.logger.info(f"{logger_header} Total time for the transfer process:{processing_time :.2f}[sec] ")

    def liplus_transfer_tool(self, toolid, ldb_dir, reg_folder):
        self.toolid = toolid  # 装置名 (MachineName)
        self.ldb_dir = ldb_dir  # LiplusDBサーバのデータ転送先 (LiplusDB transfer target. *[CSV 5th column])
        self.reg_folder = reg_folder  # 正規フォルダパス (* Liplus Data Download Folder)

        logger_header = f"[{self.toolid}]"
        liplus_transfer_log_path = os.path.dirname(FILE_LOG_LIPLUS_TRANSFER_PATH.format(f"_{self.pno}"))
        self.logger.info(f"{logger_header} LiplusTransfer_Tool.bat start!!")

        ldb_dir = ldb_dir.replace("\\", "/")
        ldb_dit_split = ldb_dir.split("/", 4)
        remote_liplus_ip = ldb_dit_split[2]
        remote_liplus_dir = "/liplus/" + ldb_dit_split[4]
        ldb_user = get_ini_value(config_ini, "LIPLUS", "LIPLUS_LDB_USER")

        # Liplus Data Download Folder
        if reg_folder == "":
            self.reg_folder = LIPLUS_REG_FOLDER_DEFAULT + "/" + self.toolid

        # rem debug --------------
        self.logger.info(f"{logger_header} REMOTE_LIPLUS_IP: {remote_liplus_ip}")
        self.logger.info(f"{logger_header} REMOTE_LIPLUS_DIR: {remote_liplus_dir}")
        self.logger.info(f"{logger_header} REG_FOLDER: {self.reg_folder}")

        # reg_folder check
        if not os.path.exists(self.reg_folder):
            self.logger.warn(f"{logger_header} f{reg_folder} folder not found")
            return

        # ssh folder check
        try:
            ssh_client = SSHManager(self.logger)
            ssh_client.create_ssh_client(ip=remote_liplus_ip, username=ldb_user, sshkey_path=self.sshkey_path)
            is_exist_target_folder = ssh_client.sftp_exists(remote_path=remote_liplus_dir)
            ssh_client.close()
            if not is_exist_target_folder:
                self.logger.error(f"{logger_header} LiplusDB transfer target folder not exist. '{remote_liplus_dir}'. end processing")
                return
        except Exception as ex:
            self.logger.error(f"{logger_header} LiplusDB transfer target folder check error. {ex}")
            return

        list_dir = os.listdir(self.reg_folder)
        list_dir_sep = "\n".join(list_dir)
        self.logger.info(f"{logger_header} dir '{self.reg_folder}' : {list_dir}")
        self.write_to_file(f"{liplus_transfer_log_path}/list_{self.pno}.txt", list_dir_sep)

        # Check 7zip
        check7zip = subprocess.call(['7z', "i"], stdin=None, stdout=subprocess.DEVNULL, stderr=None, shell=True)
        if check7zip != 0:
            self.logger.error(f"{logger_header} errorcode:1001 msg:7Zip command does not exist.")
            return

        for filename in list_dir:
            file = self.reg_folder + "/" + filename
            unzip_dir = self.reg_folder + "/" + filename + "_temp"

            # Unzip File
            unzip_start_time = time.time()
            unzip_cmd = ['7z', 'x', '-aoa', f'-o{unzip_dir}', file]
            unzip_ret = unzip(self.logger, unzip_cmd)

            # if unzip success, 0 returned.
            if unzip_ret != 0:
                self.logger.warn(f"{logger_header} The zip file is corrupted.")
                break  # if unzip fail, then loop end

            # Unzipping time
            unzip_end_time = time.time()
            unzip_time = unzip_end_time - unzip_start_time
            self.logger.info(f"{logger_header} Unzipping time of a '{file}':{unzip_time:.3f}[sec]")

            # ZIP File Remove todo 원본은 여기서 지우는데 올바를까?
            # if os.path.exists(file):
            #     self.logger.info(f"{logger_header} rmdir '{file}'")
            #     os.remove(file)

            # File transfer starts.
            self.logger.info(f"{logger_header} file transfer starts.")
            transfer_start = time.time()

            try:
                # scp transfer
                ssh_client = SSHManager(self.logger)
                ssh_client.create_ssh_client(ip=remote_liplus_ip, username=ldb_user, sshkey_path=self.sshkey_path)
                ssh_client.send_all_file(local_folder=unzip_dir, remote_folder=remote_liplus_dir)
                ssh_client.close()

                # SCP Transfer Success
                self.logger.info(f"{logger_header} SCP transfer success. '{file}'")
            except Exception as ex:
                # SCP Transfer Fail
                self.logger.error(f"{logger_header} errorcode:3000 msg:SCP transfer of '{file}' failed. {ex}")

            # SCP Transfer Time
            transfer_end = time.time() - transfer_start
            self.logger.info(f"{logger_header} SCP transfer time to LiplusDB server: :{transfer_end:.3f}[sec]")

            # Unzip Folder Remove
            self.logger.info(f"{logger_header} rmdir '{unzip_dir}'")
            rmdir_func(self.logger, unzip_dir)

        self.logger.info(f"{logger_header} LiplusTransfer_Tool Finished")

    def write_to_file(self, file_name, content):
        with open(file_name, 'w') as log_file:
            log_file.write(content)
