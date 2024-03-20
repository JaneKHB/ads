import logging.handlers
import os

import config.app_config as config
import util.time_util as time_util

class Setting:
    """로거 세팅 클래스
        ::
            Setting.LEVEL = logging.INFO # INFO 이상만 로그를 작성
    """
    def __init__(self, log_path):
        self.LEVEL = logging.INFO
        self.FILENAME = log_path
        self.MAX_BYTES = config.FILE_LOG_MAXBYTE
        self.BACKUP_COUNT = config.FILE_LOG_BACKUPCOUNT
        self.FORMAT = config.FILE_LOG_FORMAT

def Logger(name, setting):
    """파일 로그 클래스
        :param name: 로그 이름
        :type name: str
        :return: 로거 인스턴스
        ::
            logger = Logger(__name__)
            logger.info('info 입니다')
    """

    # 로거 & 포매터 & 핸들러 생성
    logger = logging.getLogger(name)
    formatter = logging.Formatter(setting.FORMAT)
    formatter.default_msec_format = time_util.TIME_FORMAT_1
    # streamHandler = logging.StreamHandler()
    ### when param ###
    # second - s
    # minute - m
    # hour - h
    # day - d
    # weekday - w0-w6 (0=monday)
    # midnight
    rotatingHandler = logging.handlers.TimedRotatingFileHandler(
        when="d",
        interval=1,
        filename=setting.FILENAME,
        backupCount=setting.BACKUP_COUNT)
    rotatingHandler.suffix = config.FILE_LOG_DATEFMT

    # 핸들러 & 포매터 결합
    # streamHandler.setFormatter(formatter)
    rotatingHandler.setFormatter(formatter)

    # 로거 & 핸들러 결합
    # logger.addHandler(streamHandler)
    logger.addHandler(rotatingHandler)

    # 로거 레벨 설정
    logger.setLevel(setting.LEVEL)

    return logger