import os
import subprocess

from config.app_config import D_ERROR, D_SUCCESS, FDT_FCS_HOME_DIR, FDT_MOVEINORDEROFOLDNESSPATH, devlog_dir
from service.common.common_service import rmdir_func


def javaif_execute(logger, modelid, toolid, reg_folder, eesp_var):
    # todo 일단 eesp_var로 옮기는게 안되서 그냥 삭제만 시키는걸 추가함.
    rtn = rmdir_func(logger, reg_folder)
    return rtn

    # todo
    moveinorderofoldnesspath = FDT_MOVEINORDEROFOLDNESSPATH

    log_dir = devlog_dir
    os.makedirs(log_dir, exist_ok=True)
    log_name = f"fcsload_{toolid}.log"

    fcs_home = FDT_FCS_HOME_DIR
    fcs_lib = os.path.join(fcs_home, "lib")
    fcs_log_conf = f"{toolid}.logcollect.logging.properties"

    subprocess_command = None

    if modelid == 1:
        # MoveInOrderOfOldness.jar 30 %REG_FOLDER% %EESP_VAR%\%TOOLID%_TMP %LOG_DIR%\%LOG_NAME%
        subprocess_command = [f"java",
                              f"-jar",
                              f"{moveinorderofoldnesspath}",
                              f"30",
                              f"{reg_folder}",
                              f"{eesp_var}{os.sep}{toolid}_TMP",
                              f"{log_dir}{os.sep}{log_name}"]

    elif modelid == 2:
        # java -Djp.canon.cks.eesp.fcs_home=%FCS_HOME% -Djp.canon.cks.eesp.eesp_var=%EESP_VAR% -Djava.utils.logging.config.file=%FCS_HOME%\conf\%FCS_LOG_CONF% -cp %FCS_LIB%\fcs.jar jp.co.canon.cks.eesp.fcs.logcollect.otslog.OTSLogCollectMain %REG_FOLDER% %TOOLID%
        subprocess_command = [f"java",
                              f"-Djp.canon.cks.eesp.fcs_home={fcs_home}",
                              f"-Djp.canon.cks.eesp.eesp_var={eesp_var}",
                              f"-Djava.util.logging.config.file={fcs_home}{os.sep}conf{os.sep}{fcs_log_conf}",
                              f"-cp",
                              f"{fcs_lib}{os.sep}fcs.jar jp.co.canon.cks.eesp.fcs.logcollect.otslog.OTSLogCollectMain",
                              f"{reg_folder}",
                              f"{toolid}"]
    elif modelid == 3:
        # java -Djp.canon.cks.eesp.fcs_home=%FCS_HOME% -Djp.canon.cks.eesp.eesp_var=%EESP_VAR% -Djava.utils.logging.config.file=%FCS_HOME%\conf\%FCS_LOG_CONF% -cp %FCS_LIB%\fcs.jar jp.co.canon.cks.eesp.fcs.logcollect.otslog.OTSLogCollectMain %REG_FOLDER%_ComErr %TOOLID%
        subprocess_command = [f"java",
                              f"-Djp.canon.cks.eesp.fcs_home={fcs_home}",
                              f"-Djp.canon.cks.eesp.eesp_var={eesp_var}",
                              f"-Djava.util.logging.config.file={fcs_home}{os.sep}conf{os.sep}{fcs_log_conf}",
                              f"-cp",
                              f"{fcs_lib}{os.sep}fcs.jar jp.co.canon.cks.eesp.fcs.logcollect.otslog.OTSLogCollectMain",
                              f"{reg_folder}_ComErr",
                              f"{toolid}"]
    else:
        logger.error(":echod MODELIDが間違ってます")

    if subprocess_command is not None:
        try:
            subprocess.run(subprocess_command, check=True)
        except subprocess.CalledProcessError as e:
            return D_ERROR
        except Exception as e:
            logger.error(9001, str(e))
            return D_ERROR
        else:
            return D_SUCCESS
    return D_ERROR
