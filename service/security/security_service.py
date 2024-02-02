import os

import pandas as pd

from config.app_config import D_SUCCESS, D_ERROR


def security_info(logger, espaddr, securityinfo_path, securitykey_path):
    twofactor = {}

    if not os.path.exists(securityinfo_path):
        return D_SUCCESS, twofactor

    security_df = pd.read_csv(securityinfo_path, names=["espaddr", "cacert", "cert", "key"], encoding='shift_jis', skiprows=2, sep=',', index_col=False, dtype=str)
    security_df = security_df[security_df["espaddr"] == espaddr]
    if not security_df.empty:
        rtn = 0
        cacert = security_df["cacert"].values[0]
        cert = security_df["cert"].values[0]
        key = security_df["key"].values[0]

        if not os.path.exists(os.path.join(securitykey_path, cacert)):
            logger.error(1003, "CA certificate file does not exist")
            return 1003, dict()

        if not os.path.exists(os.path.join(securitykey_path, cert)):
            logger.error(1004, "Client certificate file does not exist.")
            return 1004, dict()

        if not os.path.exists(os.path.join(securitykey_path, key)):
            logger.error(1005, "Private key file does not exist.")
            return 1005, dict()

        twofactor["cacert"] = os.path.join(securitykey_path, cacert)
        twofactor["cert"] = os.path.join(securitykey_path, cert)
        twofactor["key"] = os.path.join(securitykey_path, key)

    return D_SUCCESS, twofactor