import signal
import time
import sys

from datetime import datetime
from pathlib import Path

exit_flag = False   # subprocess Exit Flag

def SignalHandler(signum, frame):
    signal_name_map = {getattr(signal, name): name for name in dir(signal) if name.startswith('SIG')}
    signal_name = signal_name_map.get(signum, f'Unknown signal ({signum})')

    global exit_flag
    exit_flag = True

def delete_file(target_path, storage_period):

    target = Path(target_path)
    # target path가 디렉토리인경우
    # 디렉토리 안의 파일들 루프 돌며 재귀함수
    if target.is_dir():
        for f in target.iterdir():
            delete_file(f.absolute(), storage_period)
    else:
        # 마지막 수정시간이 storage_period 이상 지났으면 삭제
        last_modify_date = datetime.fromtimestamp(target.stat().st_mtime)
        if (datetime.now() - last_modify_date).days > storage_period:
            target.unlink()

def run(target_path, storage_period, time_interval):

    if target_path is None:
        return

    target = Path(target_path)
    if not target.is_dir():
        return

    while not exit_flag:

        delete_file(target_path, storage_period)

        # 1시간마다 실행
        time.sleep(time_interval)

# argv[1] -> target path
# argv[2] -> storage_period
# argv[3] -> time_interval
if __name__ == '__main__':

    signal.signal(signal.SIGINT, SignalHandler)
    signal.signal(signal.SIGTERM, SignalHandler)

    target_path = None
    storage_period = 30
    time_interval = 60 * 60

    if len(sys.argv) > 3:
        target_path = sys.argv[1]
        storage_period = sys.argv[2]
        time_interval = sys.argv[3]
    elif len(sys.argv) > 2:
        target_path = sys.argv[1]
        storage_period = sys.argv[2]
    elif len(sys.argv) > 1:
        target_path = sys.argv[1]

    run(target_path, storage_period, time_interval)