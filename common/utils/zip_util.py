import os
import zipfile
import time

import common.decorators.common_deco as common

# 압축파일 경로에 같은 이름폴더 아래에 압축해제.
def unzip_r(file, dest):
    path = os.path.abspath(file)
    unzip_dest = os.path.join(dest, os.path.basename(file).replace('.zip', ''))
    root_dir = unzip(path, unzip_dest)

    def recursive(parent_dir):
        if os.path.isfile(parent_dir):
            return
        for _child in os.listdir(parent_dir):
            child = os.path.join(parent_dir, _child)
            if os.path.isfile(child):
                if zipfile.is_zipfile(child):
                    child_dir = unzip(child)
                    recursive(child_dir)
                    os.remove(child)
                else:
                    recursive(child)
            else:
                recursive(child)

    recursive(root_dir)
    return unzip_dest


@common.check_process_time
# dest에 그냥 압축해제(압축파일과 같은이름의 폴더 생성x)
# dest None일시 압축파일과 같은경로에 같은이름의 폴더생성후 압축해제
def unzip(logger, zip_file, dest=None):
    dest_dir = dest
    if dest_dir is None:
        _dest = os.path.splitext(os.path.basename(zip_file))[0]
        dest_dir = os.path.join(os.path.dirname(zip_file), _dest)

    # print('dest_dir=%s' % dest_dir)
    zf = zipfile.ZipFile(zip_file)
    zf.extractall(dest_dir)
    zf.close()

    unzip_restore_timestamp(zip_file, dest_dir)
    return dest_dir


# Restores the timestamps of zipfile contents.
def unzip_restore_timestamp(zipname, extract_dir):
    for f in zipfile.ZipFile(zipname, 'r').infolist():
        # path to this extracted f-item
        fullpath = os.path.join(extract_dir, f.filename)
        if os.path.isfile(fullpath):
            # still need to adjust the dt o/w item will have the current dt
            date_time = time.mktime(f.date_time + (0, 0, -1))
            # update dt
            os.utime(fullpath, (date_time, date_time))

@common.check_process_time
def zip_files(source_dir, output_filename):
    relroot = os.path.abspath(os.path.join(source_dir, os.pardir))
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename):
                    arcname = os.path.join(os.path.relpath(root, relroot), file)
                    zip_file.write(filename, arcname)
