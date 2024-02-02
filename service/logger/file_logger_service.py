import os
import logging
import logging.handlers
import multiprocessing
from sys import platform

import psutil

import config.app_config as config


class FileLogger:
    """
    LOGをファイル形式に保存する。
    """
    _instance = None

    @classmethod
    def _get_instance(cls):
        return cls._instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls._instance = cls(*args, **kargs)
        cls.instance = cls._get_instance
        return cls._instance

    def __init__(self):
        self.queue = multiprocessing.Queue(-1)

    def listener_configurer(self, debug):
        if not debug:
            logger = logging.getLogger(config.FILE_LOG)
            logger.setLevel(logging.DEBUG)

            path = os.path.abspath(os.getcwd())
            logpath = os.path.join(path, config.FILE_LOG_FILEPATH)
            if not os.path.exists(logpath):
                os.mkdir(logpath)

            filename = os.path.join(logpath, config.FILE_LOG_FILENAME)
            dev_file_handler = logging.handlers.RotatingFileHandler(filename,
                                                                    maxBytes=config.FILE_LOG_MAXBYTE,
                                                                    backupCount=config.FILE_LOG_BACKUPCOUNT)
            dev_file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(fmt=config.FILE_LOG_FORMAT,
                                          datefmt=config.FILE_LOG_DATEFMT)
            dev_file_handler.setFormatter(formatter)
            logger.addHandler(dev_file_handler)
        else:
            logger = logging.getLogger(config.FILE_LOG)
            logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            formatter = logging.Formatter(fmt=config.FILE_LOG_FORMAT,
                                          datefmt=config.FILE_LOG_DATEFMT)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

    def logging_process(self, queue, debug, pid):
        self.listener_configurer(debug)

        path = os.path.abspath(os.getcwd())
        logpath = os.path.join(path, config.FILE_LOG_FILEPATH)

        while True:
            try:
                if psutil.pid_exists(pid):
                    record = queue.get(timeout=5)
                    logger = logging.getLogger(config.FILE_LOG)
                    logger.handle(record)  # No level or filter logic applied - just do it!

                    # win32 platform LOG Print to Terminal
                    if platform == 'win32':
                        if "WARNING: This is a development server." in record.msg:
                            record.msg = record.msg.replace("WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.", "")
                        print(f"[win32] [{record.module}] [{record.name}] [{record.msg}]")

                    if hasattr(record, 'file') and not debug:
                        logger = logging.getLogger('sep_file')
                        while logger.hasHandlers():
                            logger.removeHandler(logger.handlers[0])

                        if hasattr(record, 'path'):
                            if record.path is not None:
                                if not os.path.exists(record.path):
                                    os.mkdir(record.path)
                                filename = os.path.join(record.path, record.file)
                            else:
                                filename = os.path.join(logpath, record.file)
                        else:
                            filename = os.path.join(logpath, record.file)

                        fh = logging.FileHandler(filename=filename)
                        fh.setLevel(logging.DEBUG)
                        formatter = logging.Formatter(fmt=config.FILE_LOG_FORMAT,
                                                      datefmt=config.FILE_LOG_DATEFMT)
                        fh.setFormatter(formatter)
                        logger.addHandler(fh)
                        logger.handle(record)
                else:
                    logger = logging.getLogger(config.FILE_LOG)
                    logger.info('pid is not exist.')
                    return

            except Exception as e:
                # print('logging exception:', str(e))
                pass

    def worker_configurer(self, queue):
        handler = logging.handlers.QueueHandler(queue)
        logger = logging.getLogger(config.FILE_LOG)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        return logger


def init_file_log():
    """
    LOGをファイル形式に保存する。
    """
    logging_queue = FileLogger.instance().queue
    listener = multiprocessing.Process(target=FileLogger.instance().logging_process,
                                       args=(logging_queue, False, os.getpid()))
    listener.daemon = True
    listener.start()

    handler = logging.handlers.QueueHandler(logging_queue)  # Just the one handler needed
    logger = logging.getLogger(config.FILE_LOG)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    logger_werkzeug = logging.getLogger('werkzeug')
    logger_werkzeug.addHandler(handler)
