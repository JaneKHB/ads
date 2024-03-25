import datetime
import os
import shutil

import config.app_config as config
import util.time_util as time_util

def check_capacity(bat_name):
    stat = shutil.disk_usage(config.CHECK_CAPA_DRIVE)
    current_per = stat.free / stat.total * 100
    log_path = os.path.join(config.CHECK_CAPA_CURRENT_DIR, "logs", "Disk_Limit.log")

    if current_per < config.CHECK_CAPA_LIMIT_PERCENT:
        input_data = f"{bat_name}\n" \
                     f"{datetime.datetime.now().strftime(time_util.TIME_FORMAT_1)[:-4]}" \
                     f"{config.CHECK_CAPA_DRIVE} の空き容量は {current_per} ％です\n" \
                     f"空き容量がリミットを下回ったので処理を終了します\n"

        with open(log_path, "a") as f:
            f.write(input_data)
        return False

    return True
