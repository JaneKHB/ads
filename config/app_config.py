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

# -------------------Path-----------------------
# ----------------------------------------------
# Program固定Path
config_ini = "/ADS/appsrc/config/config.ini"
devlog_dir = "/ADS/devlog"

CURRENT_PATH = "/ADS/"
CONFIG_PATH = "/ADSconfiguration/"

ORIGINAL_SOURCE_PATH = CONFIG_PATH + "appsrc/"

CHECK_CAPA_DRIVE = CURRENT_PATH
CHECK_CAPA_CURRENT_DIR = CURRENT_PATH + "Capacity_Check/"
CHECK_CAPA_LIMIT_PERCENT = 5

CSV_ORIGINAL_PATH = CONFIG_PATH + "originalcsv/"
CSV_REAL_PATH = CURRENT_PATH + "csv/"

# FDT path
FDT_TOOL_CSV = CSV_REAL_PATH + "ToolInfo.csv"
FDT_UPTOOL_CSV = CSV_REAL_PATH + "UpToolInfo.csv"
FDT_CURRENT_DIR = CURRENT_PATH + "fdt_batch/"

FDT_ADS2_FOLDER = "/ADS/LOG/temp"
FDT_ADS2_UPLOAD = "/ADS/LOG/Upload"

FDT_FCS_HOME = CURRENT_PATH + "fcs/"
FDT_MOVEINORDEROFOLDNESSPATH = "/ADS/MoveInOrderOfOldness.jar"

FDT_FPA_TRACE_REG_FOLDER = "/ADS/var/fpatrace"

FDT_UP_CURRENT_DIR = "/ADS/UploadBatch/"
FDT_UP_DIR = "/ADS/FSLOG/uploads"

# Liplus path
LIPLUS_CURRENT_DIR = CURRENT_PATH + "Liplus_batch/"
LIPLUS_DOWNLOAD_CURRENT_DIR = CURRENT_PATH + "OnDemandCollectDownload/"
LIPLUS_UPLOAD_CURRENT_DIR = CURRENT_PATH + "CollectRequestFileUpload/"
LIPLUS_ONDEMAND_DIR = CURRENT_PATH + "ondemand/"
LIPLUS_REG_FOLDER_DEFAULT = CURRENT_PATH + "Liplus_LOG/"
LIPLUS_REG_FOLDER_TMP = CURRENT_PATH + "Liplus_TMP/"

LIPLUS_TOOL_CSV = CSV_REAL_PATH + "LiplusToolInfo{}.csv"
LIPLUS_DOWNLOAD_INFO_CSV = CSV_REAL_PATH + "DownloadInfo.csv"
LIPLUS_UPLOAD_INFO_CSV = CSV_REAL_PATH + "UploadInfo.csv"
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
SECURITYINFO_PATH = CSV_ORIGINAL_PATH + "SecurityInfo.csv"

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
FS_ROOT = CURRENT_PATH + 'appsrc/'
PROCESS_SCRIPT = 'process_main.py'

# ----------------------------------------------
# Log System Settings
FILE_LOG = 'APP_LOG'
FILE_LOG_PATH = CURRENT_PATH + 'devlog/'
FILE_LOG_LIPLUS_PATH = FILE_LOG_PATH + 'Liplus/'
FILE_LOG_MAIN_PATH = FILE_LOG_PATH + 'ads_dev_log.log'
FILE_LOG_SETUP_CSV_PATH = CONFIG_PATH + 'setup_csv_log/setup_csv.log'
FILE_LOG_LIPLUS_GET_PATH = FILE_LOG_LIPLUS_PATH + 'liplus_get{}.log'
FILE_LOG_LIPLUS_TRANSFER_PATH = FILE_LOG_LIPLUS_PATH + 'liplus_transfer{}.log'
FILE_LOG_LIPLUS_DOWNLOAD_PATH = FILE_LOG_LIPLUS_PATH + 'liplus_download.log'
FILE_LOG_LIPLUS_UPLOAD_PATH = FILE_LOG_LIPLUS_PATH + 'liplus_upload.log'
FILE_LOG_LIPLUS_FILE_TRANSFER = FILE_LOG_LIPLUS_PATH + 'file_transfer.log'
FILE_LOG_MAXBYTE = 10 * 1024 * 1024
FILE_LOG_BACKUPCOUNT = 100
FILE_LOG_FORMAT = '%(asctime)s [%(levelname)8s | %(name)6s, %(module)s(%(lineno)3s)] --- %(message)s'
FILE_LOG_FILE_SIZE_FORMAT = '%(asctime)s,%(name)s,%(message)s'
FILE_LOG_DATEFMT = '%Y%m%d'

LOG_NAME_LIPLUS_DOWN = "LIPLUS_DOWN"
LOG_NAME_LIPLUS_GET = "LIPLUS_GET"
LOG_NAME_LIPLUS_TRANSFER = "LIPLUS_TRANSFER"
LOG_NAME_LIPLUS_UPLOAD = "LIPLUS_UPLOAD"
LOG_NAME_SETUP_CSV = "SETUP_CSV"
LOG_NAME_FDT_DOWN = "FDT_DOWN"
