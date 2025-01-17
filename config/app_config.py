# ----------------------------------------------
APP_VERSION = "0.0.1"

# ----------------------------------------------
# Database config for ADS server
# ADS_DB = {'dbname': "adsdb",
#           'user': "adsadmin",
#           'host': "localhost",
#           'password': "canon",
#           'port': 5432}
# ADS_DB_SCHEMA_NAME = 'ads_db'
# ADS_DB_SCHEMA = {**ADS_DB, 'schema': ADS_DB_SCHEMA_NAME}

# -------------------Path-----------------------
# ----------------------------------------------
# Program固定Path
config_ini = "/ADS/appsrc/config/config.ini"
devlog_dir = "/ADS/devlog"

CURRENT_DIR = "/ADS/"
CONFIG_DIR = "/ADSconfiguration/"

ORIGINAL_SOURCE_DIR = CONFIG_DIR + "appsrc/"

CHECK_CAPA_DRIVE_DIR = CURRENT_DIR
CHECK_CAPA_CURRENT_DIR = CURRENT_DIR + "capacity_check/"
CHECK_CAPA_LIMIT_PERCENT = 5

CSV_ORIGINAL_DIR = CONFIG_DIR + "originalcsv/"
CSV_REAL_DIR = CURRENT_DIR + "csv/"

# FDT path
FDT_TOOL_CSV_PATH = CSV_REAL_DIR + "ToolInfo.csv"
FDT_UPTOOL_CSV_PATH = CSV_REAL_DIR + "UpToolInfo.csv"
FDT_CURRENT_DIR = CURRENT_DIR + "fdt_batch/"

FDT_ADS2_FOLDER_DIR = "/ADS/LOG/temp/"
FDT_ADS2_UPLOAD_DIR = "/ADS/LOG/upload/"

FDT_FCS_HOME_DIR = CURRENT_DIR + "fcs/"
FDT_MOVEINORDEROFOLDNESSPATH = "/ADS/MoveInOrderOfOldness.jar"

FDT_FPA_TRACE_REG_FOLDER_DIR = "/ADS/var/fpatrace/"

FDT_UP_CURRENT_DIR = "/ADS/uploadbatch/"
FDT_UP_DIR = "/ADS/FSLOG/uploads/"

# Liplus path
LIPLUS_CURRENT_DIR = CURRENT_DIR + "liplus_batch/"
LIPLUS_DOWNLOAD_CURRENT_DIR = CURRENT_DIR + "download/"
LIPLUS_UPLOAD_CURRENT_DIR = CURRENT_DIR + "upload/"
LIPLUS_ONDEMAND_DIR = CURRENT_DIR + "ondemand/"
LIPLUS_REG_FOLDER_DEFAULT_DIR = CURRENT_DIR + "liplus_lOG/"
LIPLUS_REG_FOLDER_TMP_DIR = CURRENT_DIR + "liplus_tmp/"

LIPLUS_TOOL_CSV_PATH = CSV_REAL_DIR + "LiplusToolInfo{}.csv"
LIPLUS_DOWNLOAD_INFO_CSV_PATH = CSV_REAL_DIR + "DownloadInfo.csv"
LIPLUS_UPLOAD_INFO_CSV_PATH = CSV_REAL_DIR + "UploadInfo.csv"
# ----------------------------------------------
# ----------------------------------------------

# -----------------CSV Param--------------------
# ----------------------------------------------
# FDT
# CSV ファイルHeader設定
FDT_TOOL_INFO_HEADER = ["toolid", "modelid", "espaddr", "cntlmt", "otsname",
                        "otsipaddr", "reg_folder", "userid", "userpasswd", "backup_dir", "wait_time"]
FDT_TOOL_DATA_TYPE = {"toolid": str, "modelid": int, "espaddr": str, "cntlmt": int, "otsname": str,
                      "otsipaddr": str, "reg_folder": str, "userid": str, "userpasswd": str, "backup_dir": str, "wait_time": int}

FDT_UPTOOL_INFO_HEADER = ["espaddr", "userid", "userpasswd", "toolid", "categoryid"]
FDT_UPTOOL_DATA_TYPE = {"espaddr": str, "userid": str, "userpasswd": str, "toolid": str, "categoryid": str}


# LIPLUS
# CSV Header
LIPLUS_TOOL_INFO_HEADER_7 = ["ca_name", "toolid", "espaddr", "cntlmt", "ldb_dir",
                             "userid", "userpasswd"]
LIPLUS_TOOL_DATA_TYPE_7 = {"ca_name": str, "toolid": str, "espaddr": str, "cntlmt": int, "ldb_dir": str,
                           "userid": str, "userpasswd": str}

LIPLUS_TOOL_INFO_HEADER = ["ca_name", "toolid", "espaddr", "cntlmt", "ldb_dir",
                           "userid", "userpasswd", "reg_folder"]
LIPLUS_TOOL_DATA_TYPE = {"ca_name": str, "toolid": str, "espaddr": str, "cntlmt": int, "ldb_dir": str,
                         "userid": str, "userpasswd": str, "reg_folder": str}

LIPLUS_DOWNLOAD_INFO_HEADER = ["espaddr", "userid", "userpasswd", "localfab", "remotefab"]
LIPLUS_DOWNLOAD_DATA_TYPE = {"espaddr": str, "userid": str, "userpasswd": str, "localfab": str, "remotefab": str}
LIPLUS_UPLOAD_INFO_HEADER = ["espaddr", "userid", "userpasswd", "localfab", "remotefab"]
LIPLUS_UPLOAD_DATA_TYPE = {"espaddr": str, "userid": str, "userpasswd": str, "localfab": str, "remotefab": str}
# ----------------------------------------------
# ----------------------------------------------

# Security
SECURITYINFO_PATH = CSV_ORIGINAL_DIR + "SecurityInfo.csv"

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

IS_USE_WGET = True
IS_USE_UNZIP_LIB = False

# ----------------------------------------------
# Filesystem Root
FS_ROOT_DIR = CURRENT_DIR + 'appsrc/'
PROCESS_SCRIPT = 'process_main.py'

# ----------------------------------------------
# Log System Settings
FILE_LOG = 'APP_LOG'
FILE_LOG_PATH_DIR = CURRENT_DIR + 'devlog/'
FILE_LOG_LIPLUS_DIR = FILE_LOG_PATH_DIR + 'liplus/'
FILE_LOG_MAIN_PATH = FILE_LOG_PATH_DIR + 'ads_dev_log.log'
FILE_LOG_SETUP_CSV_PATH = FILE_LOG_PATH_DIR + 'setup_csv.log'
FILE_LOG_LIPLUS_GET_PATH = FILE_LOG_LIPLUS_DIR + 'liplus_get{}.log'
FILE_LOG_LIPLUS_TRANSFER_PATH = FILE_LOG_LIPLUS_DIR + 'liplus_transfer{}.log'
FILE_LOG_LIPLUS_DOWNLOAD_PATH = FILE_LOG_LIPLUS_DIR + 'liplus_download.log'
FILE_LOG_LIPLUS_UPLOAD_PATH = FILE_LOG_LIPLUS_DIR + 'liplus_upload.log'
FILE_LOG_LIPLUS_FILE_TRANSFER_PATH = FILE_LOG_LIPLUS_DIR + 'file_transfer.log'
FILE_LOG_CAPA_LOG_PATH = CURRENT_DIR + "capacity_check/" + "Disk_Limit.log"
FILE_LOG_MAXBYTE = 10 * 1024 * 1024
FILE_LOG_BACKUPCOUNT = 30
FILE_LOG_FORMAT = '%(asctime)s [%(levelname)8s | %(name)6s, %(module)s(%(lineno)3s)] --- %(message)s'
FILE_LOG_FILE_SIZE_FORMAT = '%(asctime)s,%(name)s,%(message)s'
FILE_LOG_DATEFMT = '%Y%m%d'

PROC_NAME_LIPLUS_DOWN = "LIPLUS_DOWNLOAD"
PROC_NAME_LIPLUS_GET = "LIPLUS_GET"
PROC_NAME_LIPLUS_TRANSFER = "LIPLUS_TRANSFER"
PROC_NAME_LIPLUS_UPLOAD = "LIPLUS_UPLOAD"
PROC_NAME_SETUP_CSV = "SETUP_CSV"
PROC_NAME_FDT_DOWN = "FDT_DOWN"
