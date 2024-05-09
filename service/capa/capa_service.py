import datetime
import shutil

import config.app_config as config
import common.utils.time_util as time_util
import common.loggers.common_logger as log

from service.ini.ini_service import get_ini_value

def check_capacity(bat_name):
    rtn = True
    stat = shutil.disk_usage(config.CHECK_CAPA_DRIVE_DIR)
    current_per = stat.free / stat.total * 100
    free_storage_mb = stat.free / 1024 / 1024
    # log_path = os.path.join(config.CHECK_CAPA_CURRENT_DIR, "logs", "Disk_Limit.log")
    capa_logger = log.TimedLogger("CAPACITY_CHECK", log.Setting(config.FILE_LOG_CAPA_LOG_PATH, True))

    # if current_per < config.CHECK_CAPA_LIMIT_PERCENT:
    if free_storage_mb < int(get_ini_value(config.config_ini, "GLOBAL", "HDD_MIN_MEGA_SIZE")):
        input_data = f"{bat_name}\n" \
                     f"{datetime.datetime.now().strftime(time_util.TIME_FORMAT_1)[:-4]}" \
                     f"{config.CHECK_CAPA_DRIVE_DIR} の空き容量は {free_storage_mb} MBです\n" \
                     f"空き容量がリミットを下回ったので処理を終了します\n"
        capa_logger.info(input_data)
        rtn = False

    capa_logger.handlers.clear()

    return rtn
