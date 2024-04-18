import subprocess
import os
from sys import platform

from config.app_config import D_ERROR, D_SUCCESS
from smb.SMBConnection import SMBConnection


def remote_check_folder(logger, remote_folder):
    # todo
    if platform == "win32":
        return D_SUCCESS

    return D_SUCCESS

    # khb. todo. 리눅스에 패키지(pysmb) 설치 고려해야함.
    # # SMB 연결 설정
    # try:
    #     conn = SMBConnection(remote_user, remote_password, "local_name", remote_host, use_ntlm_v2=True)
    #     conn.connect(remote_host, 445)
    #
    #     # 원격 폴더 존재 여부 확인
    #     if conn.listPath(remote_folder, "/"):
    #         print(f"The remote folder '{remote_folder}' exists.")
    #     else:
    #         print(f"The remote folder '{remote_folder}' does not exist.")
    #
    # except Exception as e:
    #     print(f"Error: {e}")
    # finally:
    #     conn.close()


def remote_check_path_by_sshkey(logger, sshkey_path, user, ip, dir):
    # todo
    if platform == "win32":
        return D_SUCCESS

    rtn, stdout, stderr = remote_ssh_command(sshkey_path, user, ip, f"test -d {dir}")
    if rtn != 0:
        logger.trace(stdout)
        logger.trace(stderr)
        return D_ERROR
    return D_SUCCESS


def remote_ssh_command(ssh_key_path, username, host, command):
    # todo
    if platform == "win32":
        return D_SUCCESS

    subprocess_command = f'ssh -i {ssh_key_path} {username}@{host} "{command}"'
    try:
        subprocess.run(subprocess_command, check=True)
    except subprocess.CalledProcessError as e:
        return D_ERROR
    except Exception as e:
        return D_ERROR
    else:
        return D_SUCCESS


def remote_scp_send_files(sshkey_path, source_folder, user, ip, dir):
    subprocess_command = [
        'scp',
        '-oStrictHostKeyChecking=no',
        '-i', sshkey_path,
        '-r', source_folder,
        f'{user}@{ip}:{dir}'
    ]
    try:
        subprocess.run(subprocess_command, check=True)
    except subprocess.CalledProcessError as e:
        return D_ERROR
    except Exception as e:
        return D_ERROR
    else:
        return D_SUCCESS


def isExistWget(logger):
    # khb. FIXME. ['wget', '-V'] 사용 시, Windows 에서는 returncode 0, Linux 에서는 returncode 1.
    # Array 가 아닌 String 으로 수정 ['wget', '-V'] => 'wget -V'
    check_cmd = 'wget -V'
    check_wget = subprocess.run(check_cmd, stdin=None, stdout=subprocess.DEVNULL, stderr=None, shell=True)

    ret = check_wget.returncode
    if ret != 0:
        logger.error("errorcode:1000 msg:Wget command does not exist.")

    return ret
