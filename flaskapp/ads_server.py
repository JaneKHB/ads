"""
================================================================================
 :mod:`ads_server` --- 基本起動を担当する。
================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2023. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import os
import shutil

from flask import Flask, make_response, send_from_directory
from flask_restx import Api
from flask_cors import CORS
from flask import request
import config.app_config as config

import logging
import logging.handlers

from controller.process_con.process_controller import ProcessNS
from service.logger.file_logger_service import init_file_log


def create_app():
    """
    AdsServerの起動処理する。

    """

    init_file_log()
    copy_process_script()

    # Instantiate flask.
    app = Flask(__name__, static_folder='../resource/static/', static_url_path='/main')

    # Request情報をLOGに保存する。
    @app.before_request
    def log_request_info():
        try:
            logger = logging.getLogger(config.FILE_LOG)
            logger.info('http| %s' % request.url)
            if request.is_json:
                data = request.json
                if data is not None:
                    logger.info('http| %s' % data)
        except:
            pass

    # ResponseからClickjacking対応
    @app.after_request
    def apply_caching(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        return response

    # App configuration
    app.config['DEBUG'] = False
    app.config.SWAGGER_UI_DOC_EXPANSION = 'none'  # none, list, full
    api = Api(app,
              doc='/doc/',
              version=config.APP_VERSION,
              title='ADS Server',
              description='Application server supporting remote service',
              license='Copyright (c) 2024 CANON Inc. All rights reserved.')
    CORS(app)

    api.add_namespace(ProcessNS, '/api/v1/process')

    # init db
    # init_db()

    @app.route('/', methods=['GET'])
    def main_page():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/api/v1/version', methods=['GET'])
    def version():
        return make_response(config.APP_VERSION, 200)

    print_url(app)
    return app


def print_url(app):
    for r in app.url_map.iter_rules():
        print("%-40s %s" % (r.methods, r.rule))


def copy_process_script():
    """
    起動してJobを処理するために別のフォルダにPythonファイルをCopyする。

    """
    print('copy files for process')
    if os.path.exists(config.PROCESS_ROOT):
        shutil.rmtree(config.PROCESS_ROOT)
    shutil.copytree('process', config.PROCESS_ROOT)

    # 【client JobのDocker削除によるMultiProcess実行】
    process_main = config.FS_ROOT_DIR + os.sep + config.PROCESS_SCRIPT
    if os.path.exists(process_main):
        os.remove(process_main)
    shutil.copy(config.PROCESS_SCRIPT, process_main)
