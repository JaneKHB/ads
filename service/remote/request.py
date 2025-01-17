import os
import time
import requests
import subprocess

import common.decorators.common_deco as common

from config.app_config import D_SUCCESS, D_ERROR

# subprocess
@common.check_process_time
def wget_by_subprocess(logger, download_cmd, retry_max, retry_sleep):
    rtn = D_ERROR
    for _ in range(retry_max):
        rtn = subprocess_run(logger, download_cmd)
        if rtn == 0:  # if download success, subprocess 0 returned.
            rtn = D_SUCCESS
            break
        else:
            logger.warn(f"Executed retry of file collection from ESP")
            time.sleep(retry_sleep)

    return rtn

@common.check_process_time
def esp_download(logger, url, fname, timeout, twofactor, retry_max, retry_sleep):
    rtn = D_ERROR

    # 정기 수집 파일 다운로드
    for _ in range(retry_max):
        rtn = _request_inner(url, fname, timeout, twofactor)
        if rtn == D_SUCCESS:
            break
        else:
            logger.warn(f"Failed to retry collecting {fname} from ESP.")
            time.sleep(retry_sleep)

    return rtn

@common.check_process_time
def esp_upload(logger, url, heaer, file, timeout, twofactor, retry_max, retry_sleep):
    rtn = D_ERROR

    for _ in range(retry_max):
        rtn = _request_multipart(url, heaer, file, timeout, twofactor)
        if rtn == D_SUCCESS:
            break
        else:
            logger.warn(f"Upload Failed. {file}.")
            time.sleep(retry_sleep)


def _request_multipart(url, header, file, timeout, twofactor):
    try:
        if len(twofactor):
            verify = twofactor["cacert"]
            cert = (twofactor["cert"], twofactor["key"])
            connect_read_timeout = (timeout, None)
            response = requests.post(url, headers=header, files=file, timeout=connect_read_timeout, stream=True,
                                verify=verify, cert=cert)
        else:
            connect_read_timeout = (timeout, None)
            response = requests.get(url, timeout=connect_read_timeout, stream=True)
    except Exception as e:
        print(str(e))
        return D_ERROR

    if response.status_code != 200:
        return D_ERROR
    return D_SUCCESS


def _request_inner(url, fname, timeout, twofactor):
    try:
        if len(twofactor):
            verify = twofactor["cacert"]
            cert = (twofactor["cert"], twofactor["key"])
            connect_read_timeout = (timeout, None)
            response = requests.get(url, timeout=connect_read_timeout, stream=True,
                                    verify=verify,
                                    cert=cert)
        else:
            connect_read_timeout = (timeout, None)
            response = requests.get(url, timeout=connect_read_timeout, stream=True)
    except Exception as e:
        print(str(e))
        return D_ERROR

    if response.status_code != 200:
        return D_ERROR

    try:
        if fname is None:
            return D_SUCCESS

        if os.path.exists(fname):
            os.remove(fname)

        dirname = os.path.dirname(fname)
        if not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)

        with open(fname, 'wb') as f:
            f.write(response.content)
    except Exception as e:
        return D_ERROR

    if not os.path.exists(fname):
        return D_ERROR

    return D_SUCCESS



def subprocess_run(logger, cmd):
    try:
        _subprocess = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
        ret = _subprocess.returncode
        return ret
    except Exception as ex:
        logger.warn(f"subprocess run unknown error. {ex}")
        return D_ERROR
