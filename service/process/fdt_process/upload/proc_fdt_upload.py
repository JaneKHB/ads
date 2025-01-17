"""
=========================================================================================
 :mod:`proc_fdt_upload` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------

import time
from typing import Union

from config.app_config import D_SHUTDOWN, D_PROC_START, D_PROC_ING, D_PROC_END, D_SUCCESS, D_REDIS_SHUTDOWN_KEY
from service.logger.db_logger_service import DbLogger
from service.process.fdt_process.upload.file_upload import FdtFileUpload

# \ADS\UploadBatch\LoopScript\Upload_Loop.bat
def fdt_upload_loop(pname, sname, pno: Union[int, None]):
    logger = DbLogger(pname, sname, pno)

    while True:
        if get_redis_global_status(D_REDIS_SHUTDOWN_KEY) == D_SHUTDOWN:
            break

            # 1Cycleを開始してもいいか確認。
            # 1Cycle을 시작할 수 있는지 확인.
            rtn, val = get_redis_process_status(pname, sname, pno)
            if rtn != D_SUCCESS or val != D_PROC_START:
                time.sleep(1)
                continue

            # Process進行中に設定
            # 프로세스 진행 중 설정
            set_redis_process_status(pname, sname, pno, D_PROC_ING)

            # Auto_Upload.bat
            obj = FdtFileUpload(logger, pname, sname, pno)
            obj.start()

            # Process進行完了を通知
            # 프로세스 진행 완료 알림
            set_redis_process_status(pname, sname, pno, D_PROC_END)

if __name__ == '__main__':
    fdt_upload_loop("FDT", "UPLOAD", None)