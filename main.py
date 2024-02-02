"""
================================================================================
 :mod:`main` --- Main
================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import os
import sys
import flaskapp.ads_server

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) + os.path.sep
sys.path.append(BASE_DIR)
os.chdir(BASE_DIR)


if __name__ == '__main__':
    app = flaskapp.ads_server.create_app()
    app.run(threaded=True, host='0.0.0.0', port=8081)
