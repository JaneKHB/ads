"""
=========================================================================================
 :mod:`process_main` --- 。
=========================================================================================
"""

# ---------------------------------------------------------------------------
# Copyright:   Copyright 2024. CANON Inc. all rights reserved.
# ---------------------------------------------------------------------------
import argparse
import os

from service.process.proc_fdt_deploy import fdt_deploy_loop
from service.process.proc_fdt_download import fdt_download_loop


def run(pname, sname, pno):
    if pname is None or sname is None or pno is None:
        print('error')

    if pname == "FDT":
        if sname == "DOWNLOAD":
            fdt_download_loop(pname, sname, 0)
        elif sname == "DEPLOY":
            fdt_deploy_loop(pname, sname, 0)
        else:
            print('error')
    elif pname == "LIPLUS":
        if sname == "GET":
            pass  # fdt_download_loop(pname, sname, 0)
        elif sname == "TRANSFER":
            pass  # fdt_deploy_loop(pname, sname, 0)
        else:
            print('error')
    else:
        print('error')

def makedir():
    # os.makedirs("D:/wget/1/2/3/4/5/6/7/8/9", exist_ok=True)
    # make directory
    pass

if __name__ == '__main__':

    # 폴더 생성
    makedir()

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--process", help="", default=None)
    parser.add_argument("-s", "--sub", help="", default=None)
    parser.add_argument("-n", "--no", help="", default=None)
    args = parser.parse_args()

    run(args.process, args.sub, args.no)
