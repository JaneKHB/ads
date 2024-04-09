import paramiko
import os
import sys
import traceback

from config.app_config import D_SUCCESS, D_ERROR


class SSHManager:
    def __init__(self, logger):
        self.ssh_client = None
        self.sftp_client = None
        self.logger = logger

    def create_ssh_client(self, ip, username, sshkey_path):
        try:
            if self.ssh_client is None:
                # ssh_client
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(ip, username=username, key_filename=sshkey_path)

                # sftp_client
                self.sftp_client = self.ssh_client.open_sftp()
            else:
                self.logger.warn("SSH client session exist.")
        except Exception as ex:
            raise ex

    def close(self):
        self.ssh_client.close()
        self.sftp_client.close()

    def send_all_file(self, local_folder, remote_folder):
        try:
            local_file_list = os.listdir(local_folder)
            for filename in local_file_list:
                file = str(f"{local_folder}{os.sep}{filename}")
                self.sftp_client.put(file, remote_folder + "/" + filename)
        except Exception as ex:
            raise ex

    def sftp_exists(self, remote_path):
        try:
            self.sftp_client.stat(remote_path)
            return True
        except (Exception,):
            return False
