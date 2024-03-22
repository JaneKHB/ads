import os
import psycopg2 as pg2

from config.app_config import ADS_DB, ADS_DB_SCHEMA_NAME


def db_file_download_log(pname, sname, pno, fname, fsize, tick_time_sub):
    # print(f"ESP File={pname}:{sname}:{pno} {fname}. size={fsize} ")
    pass

def init_db():
    # Initialize server database.
    init_schema([ADS_DB_SCHEMA_NAME])
    init_table()


def init_schema(schema_list):
    config = ADS_DB
    try:
        with pg2.connect(**config) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                # DBの全体Schema目録獲得
                cur.execute('select nspname from pg_catalog.pg_namespace')
                rows = cur.fetchall()
                # Schema生成
                for item in schema_list:
                    if (item,) not in rows:
                        cur.execute('create schema %s' % item)
                        print(item + ' schema is created!!')
    except Exception as e:
        print('schema create error!')
        print(e)


def init_table():
    config = ADS_DB
    data_path = './resource/sql/table'
    file_list = {file_name: False for file_name in os.listdir(data_path)}

    idx = 0
    loop_cnt = 0
    complete = False
    while not complete:
        if loop_cnt >= 5:
            print('table create error!')
        try:
            with pg2.connect(**config) as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    (file_name, value) = list(file_list.items())[idx]

                    if os.path.isdir(os.path.join(data_path, file_name)) is False and value is False:
                        [schema, table_name, extension] = file_name.split(sep='.')
                        print(f'DB Table file {schema}.{table_name}.sql processing')

                        cur.execute("SELECT EXISTS "
                                    "(SELECT FROM information_schema.tables WHERE table_schema='%s' AND table_name='%s')"
                                    % (schema, table_name))

                        rows = cur.fetchone()
                        if rows[0] is False:
                            file_path = os.path.join(data_path, file_name)
                            cur.execute(open(file_path, 'r').read())
                            print(schema + '.' + table_name + ' table is created!!')
                            file_list[file_name] = True
                        else:
                            file_list[file_name] = True

            if False in file_list.values():
                idx += 1
                if idx == len(list(file_list.items())):
                    idx = 0
                    loop_cnt += 1
                    print('Retry...')
            else:
                complete = True
        except Exception as msg:
            print('failed to initialize tables (%s)' % msg)
            idx += 1
            if idx == len(list(file_list.items())):
                idx = 0
                loop_cnt += 1
                print('Retry...')
