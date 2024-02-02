"""
================================================================================
 :mod:`system_logger` --- SystemLogger処理を担当している。
================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2023. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import datetime
import psycopg2 as pg2
from config.app_config import ADS_DB


class DbLogger:

    TRACE = 'TRACE'
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARN = 'WARN'
    ERROR = 'ERROR'
    FATAL = 'FATAL'

    def __init__(self, sys, module, no=0):
        self.sys = sys
        self.module = module
        self.lv = DbLogger.INFO
        self.config = ADS_DB
        self.con = pg2.connect(**self.config)
        self.con.autocommit = True
        self.cur = self.con.cursor()
        self.key = ''
        self.purge()

    def purge(self):
        try:
            if self.cur is not None:
                now = datetime.datetime.now()
                th1 = now - datetime.timedelta(days=30)
                th2 = now - datetime.timedelta(days=365)
                self.cur.execute(f"delete from ads_db.system_log \
                    where (key = '' and ts < '{th1}') or ts < '{th2}'")
        except Exception as ex:
            self.warn('failed to purge expired log (msg=%s)' % str(ex))

    def set_default_level(self, lv):
        self.lv = lv

    def set_default_key(self, key):
        self.key = key

    def log(self, msg, **kwargs):
        msg = msg.replace("'", "")
        msg = msg[:511]
        c_list = list()
        v_list = list()

        def varying_key(k, default=None):
            if k in kwargs:
                c_list.append(k)
                v_list.append(f"'{kwargs[k]}'")
            elif default is not None:
                c_list.append(k)
                v_list.append(f"'{default}'")

        varying_key('sys', default=self.sys)
        varying_key('module', default=self.module)
        varying_key('lv', default=self.lv)

        c_list.append('key')
        if 'key' in kwargs:
            v_list.append(f"'{kwargs['key']}'")
        else:
            v_list.append(f"'{self.key}'")

        try:
            self.cur.execute(f"insert into ads_db.system_log (msg, {','.join(c_list)}) "
                             f"values ('{msg}', {','.join(v_list)}) returning *")

        except Exception:
            print(f"- {msg}")
            return

        ret = self.cur.fetchone()
        try:
            print("%s: %-6.5s: %s: %s: %s" % (ret[1].strftime('%Y-%m-%d %H:%M:%S'), ret[4], ret[2], ret[6], ret[5]))
        except:
            print(f"-- {msg}")

    def info(self, msg, **kwargs):
        self.log(msg, **kwargs, lv=DbLogger.INFO)

    def warn(self, msg, **kwargs):
        self.log(msg, **kwargs, lv=DbLogger.WARN)

    def error(self, errorcode, msg, **kwargs):
        self.log(msg, **kwargs, lv=DbLogger.ERROR)

    def fatal(self, msg, **kwargs):
        self.log(msg, **kwargs, lv=DbLogger.FATAL)

    def debug(self, msg, **kwargs):
        self.log(msg, **kwargs, lv=DbLogger.DEBUG)

    def trace(self, msg, **kwargs):
        self.log(msg, **kwargs, lv=DbLogger.TRACE)

    @staticmethod
    def to_str_list(dict_list):
        """
        system_log からLogを取って各Lineを特定な形式に変換してDictで回答する。

        """
        li = list()
        try:
            for d in dict_list:
                li.append("%s: %-6.5s: %s:%s: %s"
                          % (d['ts'].strftime('%Y-%m-%d %H:%M:%S'), d['lv'], d['sys'], d['module'], d['msg']))

        except KeyError as ex:
            raise KeyError('[SystemLogger.to_str_list] key error occurs. %s' % str(ex))
        return li, dict_list[-1]["id"]
