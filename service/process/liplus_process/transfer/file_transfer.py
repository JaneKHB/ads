"""
=========================================================================================
 :mod:`file_transfer` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import os
import pandas as pd

from typing import Union
from sys import platform

import config.app_config as config
import common.decorators.common_deco as common
import common.utils as util

from service.capa.capa_service import check_capacity
from service.common.common_service import rmdir_func, get_csv_info
from service.ini.ini_service import get_ini_value
from service.remote.ssh_manager import SSHManager
from service.zip.sevenzip_service import unzip, isExist7zip

class LiplusFileTransfer:
    def __init__(self, logger, pname, sname, pno: Union[int, None]):
        self.logger = logger
        self.pname = pname
        self.sname = sname
        self.pno = pno

        self.current_dir = config.LIPLUS_CURRENT_DIR
        self.tool_df = get_csv_info("LIPLUS", "TRANSFER", self.pno)
        self.sshkey_path = get_ini_value(config.config_ini, "SECURITY", "SSHKEY_PATH")

        self.toolid = None  # 装置名 (MachineName)
        self.reg_folder = None  # 正規フォルダパス (* Liplus Data Download Folder)

    @common.check_process_time
    @common.rename(config.PROC_NAME_LIPLUS_TRANSFER)
    def start(self, logger):
        # Capacity Check
        if not check_capacity(config.PROC_NAME_LIPLUS_TRANSFER):
            return

        if self.tool_df is None:
            self.logger.warn("csv file is damaged.")
            return

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
            try:
                self._liplus_transfer_tool(elem.get('toolid'), elem.get('ldb_dir'), elem.get('reg_folder'))
            except Exception as e:
                self.logger.warn(e)

    # ADS\Liplus_batch\script\LiplusTransfer_Tool.bat
    def _liplus_transfer_tool(self, toolid, ldb_dir, reg_folder):
        self.toolid = toolid  # 装置名 (MachineName)
        self.ldb_dir = ldb_dir  # LiplusDBサーバのデータ転送先 (LiplusDB transfer target. *[CSV 5th column])
        self.reg_folder = reg_folder  # 正規フォルダパス (* Liplus Data Download Folder)

        logger_header = f"[{self.toolid}]"
        liplus_transfer_log_path = os.path.dirname(config.FILE_LOG_LIPLUS_TRANSFER_PATH.format(f"_{self.pno}"))
        self.logger.info(f"{logger_header} LiplusTransfer_Tool.bat start!!")

        ldb_dir = ldb_dir.replace("\\", "/")
        ldb_dit_split = ldb_dir.split("/", 4)
        try:
            remote_liplus_ip = ldb_dit_split[2]
            remote_liplus_dir = "/liplus/" + ldb_dit_split[4]
        except Exception as e:
            self.logger.warn(f"{logger_header} {e}")
            return
        ldb_user = get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_LDB_USER")

        # Liplus Data Download Folder
        if reg_folder == "" or pd.isna(reg_folder):
            self.reg_folder = config.LIPLUS_REG_FOLDER_DEFAULT_DIR + self.toolid

        # rem debug --------------
        self.logger.info(f"{logger_header} REMOTE_LIPLUS_IP: {remote_liplus_ip}")
        self.logger.info(f"{logger_header} REMOTE_LIPLUS_DIR: {remote_liplus_dir}")
        self.logger.info(f"{logger_header} REG_FOLDER: {self.reg_folder}")

        # reg_folder check
        if not os.path.exists(self.reg_folder):
            self.logger.warn(f"{logger_header} f{reg_folder} folder not found")
            return

        # ssh target folder check
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
        self._write_to_file(f"{liplus_transfer_log_path}/list_{self.pno}.txt", list_dir_sep)

        # Check 7zip
        if not config.IS_USE_UNZIP_LIB and isExist7zip(self.logger) != 0:
            return

        for filename in list_dir:
            file = self.reg_folder + "/" + filename
            unzip_dir = self.reg_folder + "/" + filename + "_temp"

            # Unzip File
            unzip_cmd = ['7z', 'x', '-aoa', f'-o{unzip_dir}', file]

            # khb. FIXME. 7zip 명령어(array)를 linux 에서 사용 시, 압축이 풀리지 않는 현상 발생(x 옵션이 아닌 -h 옵션이 적용되는것같음)
            # khb. FIXME. 해당 기능(7zz x -aoa ...) 에 대해서는 Array 가 아닌 String 으로 처리한다.
            if "linux" in platform:
                unzip_cmd[0] = '7zz'
                unzip_cmd = " ".join(unzip_cmd)

            self.logger.info(f"Start unzip '{file}'")
            if config.IS_USE_UNZIP_LIB:
                unzip_ret = util.zip_util.unzip(self.logger, file, unzip_dir)
            else:
                unzip_ret = unzip(self.logger, unzip_cmd)

            # if unzip success, 0 returned.
            if unzip_ret != 0:
                self.logger.warn(f"{logger_header} The zip file is corrupted.")
                break  # if unzip fail, then loop end

            # ZIP File Remove todo 원본은 여기서 지우는데 올바를까?
            # if os.path.exists(file):
            #     self.logger.info(f"{logger_header} rmdir '{file}'")
            #     os.remove(file)

            # File transfer starts.
            self.logger.info(f"{logger_header} Start file transfer from SCP to LiplusDB server.")
            # transfer_start = time.time()

            try:
                # scp transfer
                ssh_client = SSHManager(self.logger)
                ssh_client.create_ssh_client(ip=remote_liplus_ip, username=ldb_user, sshkey_path=self.sshkey_path)
                ssh_client.send_all_file(local_folder=unzip_dir, remote_folder=remote_liplus_dir, logger=self.logger)
                ssh_client.close()

                # SCP Transfer Success
                self.logger.info(f"{logger_header} SCP transfer success. '{file}'")
            except Exception as ex:
                # SCP Transfer Fail
                self.logger.error(f"{logger_header} errorcode:3000 msg:SCP transfer of '{file}' failed. {ex}")

            # SCP Transfer Time
            # transfer_end = time.time() - transfer_start
            # self.logger.info(f"{logger_header} SCP transfer time to LiplusDB server: :{transfer_end:.3f}[sec]")

            # Unzip Folder Remove
            rmdir_func(self.logger, unzip_dir)
            self.logger.info(f"{logger_header} rmdir '{unzip_dir}'")

        self.logger.info(f"{logger_header} LiplusTransfer_Tool Finished")

    def _write_to_file(self, file_name, content):
        with open(file_name, 'w') as log_file:
            log_file.write(content)
