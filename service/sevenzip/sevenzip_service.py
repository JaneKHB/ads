import subprocess


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
        logger.error(f"The zip file is corrupted. : {ex}")
        return -1


# sevenzip package
def unzip_from_7zip():
    print("")
