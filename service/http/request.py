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
    for _ in range(retry_max):
        rtn = request_inner(url, fname, timeout, twofactor)
        if rtn == D_SUCCESS:
            break
        else:
            logger.warn(f"Failed to retry collecting {fname} from ESP.")
            time.sleep(retry_sleep)

    return rtn


def request_inner(url, fname, timeout, twofactor):
    """
    request共通処理 (旧RapidのためにHTTPSの場合はHTTPSでTry->SSLErrorだけHTTPでもう一回Tryする。

    20230331 : Add Connection Error Retry

    :return: response, raise
    """
    try:
        if len(twofactor):
            verify = twofactor["cacert"]
            cert = (twofactor["cert"], twofactor["key"])
            response = requests.get(url, timeout=timeout, stream=True,
                                    verify=verify,
                                    cert=cert)
        else:
            response = requests.get(url, timeout=timeout, stream=True)
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
