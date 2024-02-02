import subprocess

from config.app_config import D_ERROR, D_SUCCESS


def ping_command(host: str, count: int):
    subprocess_command = ['ping', '-c', str(count), host]
    try:
        # check가 참이고, 프로세스가 0이 아닌 종료 코드로 종료되면, CalledProcessError 예외가 발생합니다.
        # 해당 예외의 어트리뷰트가 인자 및 종료 코드와 캡처되었다면 stdout과 stderr을 담습니다.
        subprocess.run(subprocess_command, check=True)
    except subprocess.CalledProcessError as e:
        return D_ERROR
    except Exception as e:
        return D_ERROR
    else:
        return D_SUCCESS
