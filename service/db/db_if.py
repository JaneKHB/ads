"""
=========================================================================================
 :mod:`db_if` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import inspect
from typing import Iterator, Union

import pandas as pd
import psycopg2 as pg2
import psycopg2.extras
from pandas import DataFrame

from config.app_config import ADS_DB


class DbIfBase:
    """
    PostgresにアクセスするためのIFクラス
    """
    def __init__(self):
        self.config = ADS_DB

    def _db_connector_dict(func):
        """
        DictCursorを利用してcursor作る。

        """

        def _wrapper(self, *args, **kwargs):
            with pg2.connect(**self.config) as connect:
                connect.autocommit = True
                with connect.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    arg_list = [sign for sign in inspect.signature(func).parameters]
                    if len(args) > 1:
                        for i in range(1, len(args)):
                            kwargs[arg_list[i+1]] = args[i]     # self追加によって+1する。
                    if 'conn' in arg_list:
                        kwargs['conn'] = connect
                    if 'cur' in arg_list:
                        kwargs['cur'] = cur

                    if len(args) == 0:
                        return func(self, **kwargs)
                    return func(self, *[args[0]], **kwargs)

        return _wrapper

    @_db_connector_dict
    def read_sql(self, sql, conn, cur) -> Union[DataFrame, Iterator[DataFrame]]:
        df = pd.read_sql(sql=sql, con=conn)
        return df

    @_db_connector_dict
    def execute(self, sql, conn, cur):
        cur.execute(sql)

    @_db_connector_dict
    def fetchone(self, sql, conn, cur):
        cur.execute(sql)
        row = cur.fetchone()
        return row

    @_db_connector_dict
    def fetchall(self, sql, conn, cur):
        cur.execute(sql)
        rows = cur.fetchall()
        return rows

    @_db_connector_dict
    def fetchall_column_names(self, sql, conn, cur):
        cur.execute(sql)
        column_names = [i[0] for i in cur.description]
        rows = cur.fetchall()
        return column_names, rows

    @_db_connector_dict
    def exist_table(self, schema, table, conn, cur) -> bool:
        """
        DB schema, tableが存在するか確認。

        True：存在する、False：無し
        """
        sql = f"select exists (select from information_schema.tables where (table_schema, table_name) = ('{schema}', '{table}') )"
        ret = pd.read_sql(sql, conn)    # 24P1 [Timezone] 問題無いことを確認済み
        if not ret['exists'].values[0]:
            return False
        return True

    @_db_connector_dict
    def get_primary_key_list(self, schema, table, conn, cur) -> list:
        """
        DB schema, tableのPrimaryKeyをリストを回答する。

        """
        primary_key_list = list()
        sql = f"""SELECT column_name
                        FROM information_schema.table_constraints
                        JOIN information_schema.key_column_usage
                        USING (constraint_catalog, constraint_schema, constraint_name,
                        table_catalog, table_schema, table_name)
                        WHERE constraint_type = 'PRIMARY KEY'
                        AND (table_schema, table_name) = ('{schema}', '{table}')
                        ORDER BY ordinal_position;
                        """
        cur.execute(sql)
        primary_key = cur.fetchall()

        for x in primary_key:
            if len(x):
                primary_key_list.append(x[0])
        return primary_key_list

    @_db_connector_dict
    def get_timezone(self, conn, cur) -> str:
        cur.execute("show timezone")
        row = cur.fetchone()[0]
        return row
