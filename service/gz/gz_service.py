import gzip
import os
import shutil

from config.app_config import D_ERROR, D_SUCCESS


def gz_compress(logger, gzip_folder, is_src_delete=True):
    """

    :return:
    """
    try:
        list_dir = os.listdir(gzip_folder)
        for filename in list_dir:
            file = gzip_folder + os.sep + filename
            if os.path.isfile(file) and not file.endswith("gz"):
                compressed_file = file + '.gz'
                with open(file, 'rb') as f_in, gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                if is_src_delete:
                    os.remove(file)
    except Exception as ex:
        logger.trace(str(ex))
        return D_ERROR

    return D_SUCCESS


def gz_uncompress(logger, gzip_folder, is_src_delete=True):
    try:
        list_dir = os.listdir(gzip_folder)
        for filename in list_dir:
            file = gzip_folder + os.sep + filename
            if os.path.isfile(file) and file.endswith("gz"):
                output_file = file[:-3]
                with gzip.open(file, 'rb') as f_in, open(output_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                if is_src_delete:
                    os.remove(file)
    except Exception as ex:
        logger.trace(str(ex))
        return D_ERROR

    return D_SUCCESS
