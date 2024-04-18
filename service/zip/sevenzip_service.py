import subprocess
from sys import platform

# subprocess
def isExist7zip(logger):
    check_cmd = ['7z', "i"]
    if "linux" in platform:
        check_cmd[0] = '7zz'

    check7zip = subprocess.run(check_cmd, stdin=None, stdout=subprocess.DEVNULL, stderr=None, shell=True)
    ret = check7zip.returncode
    if ret != 0:
        logger.error("errorcode:1001 msg:7Zip command does not exist.")

    return ret


# subprocess
def unzip(logger, unzip_cmd):
    # ex) unzip_cmd = [7z', 'x', '-aoa', f'-o{folder}', {file}]
    try:
        logger.info(f"unzip command: {unzip_cmd}")

        unzip_subprocess = subprocess.Popen(unzip_cmd, shell=True, stdout=subprocess.PIPE)
        output = unzip_subprocess.communicate()[0]  # waiting process(unzip) to end
        unzip_ret = unzip_subprocess.returncode

        logger.info(output.decode())
        return unzip_ret  # if unzip success, 0 returned.
    except Exception as ex:
        logger.error(f"unzip unknown error. {ex}")
        return -1


# zip package
def unzip_from_7zip():
    print("")
