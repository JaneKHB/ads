import json
import os
import time

import pandas as pd
import requests
import urllib3

from config.app_config import D_SUCCESS, D_ERROR


def esp_download(logger, url, fname, timeout, twofactor, retry_max, retry_sleep):
    rtn = D_ERROR

    # REM *** 定期収集ファイルダウンロード *****************************
    # 정기 수집 파일 다운로드
    for _ in range(retry_max):
        rtn = _request_inner(url, fname, timeout, twofactor)
        if rtn == D_SUCCESS:
            break
        else:
            # logger.warn(f"Failed to retry collecting {fname} from ESP.")
            print(f"Failed to retry collecting {fname} from ESP.")
            time.sleep(retry_sleep)

    return rtn

def esp_upload(logger, url, heaer, file, fname, timeout, twofactor, retry_max, retry_sleep):
    rtn = D_ERROR

    for _ in range(retry_max + 1):
        rtn = _request_multipart(url, heaer, file, fname, timeout, twofactor)
        if rtn == D_SUCCESS:
            break
        else:
            logger.warn(f"Upload Failed. {fname}.")
            time.sleep(retry_sleep)

def _request_multipart(url, header, file, fname, timeout, twofactor):
    try:
        if len(twofactor):
            verify = twofactor["cacert"]
            cert = (twofactor["cert"], twofactor["key"])
            connect_read_timeout = (timeout, None)
            res = requests.post(url, header=header, files=None, timeout=connect_read_timeout, stream=True, verify=verify, cert=cert)
        else:
            connect_read_timeout = (timeout, None)
            response = requests.get(url, timeout=connect_read_timeout, stream=True)
    except Exception as e:
        print(str(e))
        return D_ERROR

    if response.status_code != 200:
        return D_ERROR

    # shlee todo 로그 쌓아야함!!!!!! 다른 업로드들이랑 중복되는지 확인 후 수정
    # UploadBatch/Upload_Tool.bat - 180
    # if exist % LOGOPTION % (                                      # LOGOPTION 존재하면
    #         copy % LOGOPTION % +result.tmp % LOGOPTION %          # LOGOPTION + result.tmp 내용을 LOGOPTION 으로 덮기
    # ) else (
    # copy result.tmp % LOGOPTION %                                 # 아님 result.tmp 를 LOGOPTION으로 덮기
    # )
    return D_SUCCESS

def _request_inner(url, fname, timeout, twofactor):
    """
    request共通処理 (旧RapidのためにHTTPSの場合はHTTPSでTry->SSLErrorだけHTTPでもう一回Tryする。

    20230331 : Add Connection Error Retry

    :return: response, raise
    """
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
