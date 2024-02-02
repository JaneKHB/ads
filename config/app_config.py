# ----------------------------------------------
APP_VERSION = "0.0.1"

# ----------------------------------------------
# Database config for ADS server
ADS_DB = {'dbname': "adsdb",
          'user': "adsadmin",
          'host': "localhost",
          'password': "canon",
          'port': 5432}
ADS_DB_SCHEMA_NAME = 'ads_db'
ADS_DB_SCHEMA = {**ADS_DB, 'schema': ADS_DB_SCHEMA_NAME}

# ----------------------------------------------
# Program固定Path
config_ini = "/ADS/appsrc/config/config.ini"
devlog_dir = "/ADS/devlog"

# ----------------------------------------------
# FDT
FDT_TOOL_CSV = "/ADS/csv/ToolInfo.csv"
FDT_CURRENT_DIR = "/ADS/fdt_batch/"

FDT_ADS2_FOLDER = "/ADS/LOG/temp"
FDT_ADS2_UPLOAD = "/ADS/LOG/Upload"

FDT_FCS_HOME = "/ADS/fcs"
FDT_MOVEINORDEROFOLDNESSPATH = "/ADS/MoveInOrderOfOldness.jar"

FDT_FPA_TRACE_REG_FOLDER = "/ADS/var/fpatrace"

# CSV ファイルHeader設定
FDT_TOOL_INFO_HEADER = ["toolid", "modelid", "espaddr", "cntlmt", "otsname",
                        "otsipaddr", "reg_folder", "userid", "userpasswd", "backup_dir", "wait_time"]

FDT_TOOL_DATA_TYPE = {"toolid": str, "modelid": int, "espaddr": str, "cntlmt": int, "otsname": str,
                      "otsipaddr": str, "reg_folder": str, "userid": str, "userpasswd": str, "backup_dir": str, "wait_time": int}

# ----------------------------------------------
# Liplus
LIPLUS_CURRENT_DIR = "/ADS/Liplus_batch/"
LIPLUS_TOOL_CSV = "/ADS/csv/LiplusToolInfo%d.csv"
LIPLUS_REG_FOLDER_DEFAULT = "/ADS/Liplus_LOG"
LIPLUS_REG_FOLDER_TMP = "/ADS/Liplus_TMP"

LIPLUS_TOOL_INFO_HEADER_7 = ["ca_name", "toolid", "espaddr", "cntlmt", "ldb_dir",
                             "userid", "userpasswd"]
LIPLUS_TOOL_DATA_TYPE_7 = {"ca_name": str, "toolid": str, "espaddr": str, "cntlmt": int, "ldb_dir": str,
                           "userid": str, "userpasswd": str}

LIPLUS_TOOL_INFO_HEADER = ["ca_name", "toolid", "espaddr", "cntlmt", "ldb_dir",
                           "userid", "userpasswd", "reg_folder"]
LIPLUS_TOOL_DATA_TYPE = {"ca_name": str, "toolid": str, "espaddr": str, "cntlmt": int, "ldb_dir": str,
                         "userid": str, "userpasswd": str, "reg_folder": str}
# ----------------------------------------------
# Security
SECURITYINFO_PATH = "/ADS/csv/SecurityInfo.csv"

# ----------------------------------------------


# ----------------------------------------------
D_SUCCESS = 0
D_ERROR = -1

D_UNKNOWN_ERROR_NO = 9999

D_SHUTDOWN = 1

D_PROC_START = 1
D_PROC_ING = 2
D_PROC_END = 3

D_REDIS_SHUTDOWN_KEY = "shutdown"

# ----------------------------------------------
# Filesystem Root
FS_ROOT = '/ADS/appsrc'
PROCESS_SCRIPT = 'process_main.py'

# ----------------------------------------------
# Log System Settings
FILE_LOG = 'APP_LOG'
FILE_LOG_FILENAME = 'ads_dev_log.log'
FILE_LOG_FILEPATH = '/ADS/devlog'
FILE_LOG_MAXBYTE = 10 * 1024 * 1024
FILE_LOG_BACKUPCOUNT = 100
FILE_LOG_FORMAT = '%(asctime)s: %(levelname)s: %(module)s: %(message)s'
FILE_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'
