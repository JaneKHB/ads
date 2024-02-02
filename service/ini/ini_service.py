import configparser


def get_ini_value(path, section, key):
    config = configparser.ConfigParser()
    encoding_list = ['utf-8', 'cp949', 'shift_jis']
    for x in encoding_list:
        try:
            config.read(path, encoding=x)
        except:
            continue

    value1 = config.get(section, key)
    return value1
