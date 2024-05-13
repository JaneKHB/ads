import datetime
import os
import shutil
import sys

import config.app_config as config
import common.utils as util
import common.loggers.common_logger as log

from pathlib import Path

from service.common.common_service import rmtree
from service.ini.ini_service import get_ini_value

logger = None#log.FileLogger(config.LOG_NAME_SETUP_CSV, log.Setting(config.FILE_LOG_SETUP_CSV_PATH))

def dellink(current_dir):
    file = Path(current_dir, "module", "linklist.txt")
    read_line = []

    if file.exists():
        with open(file.absolute(), "r") as f:
            read_line = f.read().splitlines()

        for line in read_line:
            txt = Path(line)
            if txt.exists():
                txt.unlink(missing_ok=True)
                logger.info(f"delete [{txt.absolute()}]")

        file.unlink(missing_ok=True)
        logger.info(f"delete [{file.absolute()}]")

# /ADS/module/Csv_Copy.vbs
# origincsv/file.csv  , /ADSconfig/
def copy_csv(original_csv_path, base_dir):
    setting_csv_name = ""
    dir_name = ""
    csv_type = 0
    task_type = 0
    copy_from_dir = Path(config.CSV_ORIGINAL_DIR)
    copy_to_dir = Path(config.CSV_REAL_DIR)
    original_path = Path(config.CONFIG_DIR)

    if "Liplus_batch" in original_csv_path:
        # copy_from_dir = Path(copy_to_dir, "Liplus_batch")
        dir_name = "Liplus_batch"
        setting_csv_name = "LiplusToolInfo.csv"
        csv_type = 0
        task_type = 0
    elif "Liplus_batch_recovery" in original_csv_path:
        # copy_from_dir = Path(copy_to_dir, "Liplus_batch_recovery")
        dir_name = "Liplus_batch_recovery"
        setting_csv_name = "LiplusToolInfo.csv"
        csv_type = 0
        task_type = 1
    elif "CollectRequestFileUpload" in original_csv_path:
        # copy_from_dir = Path(copy_to_dir, "CollectRequestFileUpload")
        dir_name = "CollectRequestFileUpload"
        setting_csv_name = "UploadInfo.csv"
        csv_type = 1
        task_type = 2
    elif "UploadBatch" in original_csv_path:
        # copy_from_dir = Path(copy_to_dir, "UploadBatch")
        dir_name = "UploadBatch"
        setting_csv_name = "UploadInfo.csv"
        csv_type = 1
        task_type = 3
    elif "OnDemandCollectDownload" in original_csv_path:
        # copy_from_dir = Path(copy_to_dir, "OnDemandCollectDownload")
        dir_name = "OnDemandCollectDownload"
        setting_csv_name = "DownloadInfo.csv"
        csv_type = 1
        task_type = 4
    elif "fdt_batch" in original_csv_path:
        # copy_from_dir = Path(copy_to_dir, "fdt_batch")
        dir_name = "fdt_batch"
        setting_csv_name = "ToolInfo.csv"
        csv_type = 1
        task_type = -1
    elif "else_file" in original_csv_path:
        csv_type = -1

    # os.makedirs(copy_from_dir.absolute(), exist_ok=True)
    # logger.info(f"make dir [{copy_from_dir.absolute()}]")
    if not copy_to_dir.exists():
        copy_to_dir.mkdir(exist_ok=True)
        logger.info(f"make dir [{copy_to_dir.absolute()}]")

    # 設定ファイルの存在しないScriptに関しては何もせずコピー
    # 설정 파일이 존재하지 않는 Script에 관해서는 아무것도하지 않고 복사
    # shlee 복사 안해도 될듯. csv이외 bat, vbs복사하는부분.
    if csv_type == -1:
        # 복사는 안하고 그냥 폴더만 생성.
        autocc_loop = Path(copy_to_dir.parent, "AutoCC_Loop")
        liplus_log = Path(copy_to_dir.parent, "Liplus_LOG")
        log = Path(copy_to_dir.parent, "LOG")
        loop_script = Path(copy_to_dir.parent, "LoopScript")
        capacity_check = Path(copy_to_dir.parent, "Capacity_Check")

        autocc_loop.mkdir(exist_ok=True)
        liplus_log.mkdir(exist_ok=True)
        log.mkdir(exist_ok=True)
        loop_script.mkdir(exist_ok=True)
        capacity_check.mkdir(exist_ok=True)

        # shutil.copytree(os.path.join(copy_to_dir, "Original_Setup_File", "AutoCC_Loop"), copy_to_dir)
        # logger.info(f"copytree [{os.path.join(copy_to_dir, 'Original_Setup_File', 'AutoCC_Loop')}] -> [{copy_to_dir}]")
        #
        # shutil.copytree(os.path.join(copy_to_dir, "Original_Setup_File", "Liplus_LOG"), copy_to_dir)
        # logger.info(f"copytree [{os.path.join(copy_to_dir, 'Original_Setup_File', 'Liplus_LOG')}] -> [{copy_to_dir}]")
        #
        # shutil.copytree(os.path.join(copy_to_dir, "Original_Setup_File", "LOG"), copy_to_dir)
        # logger.info(f"copytree [{os.path.join(copy_to_dir, 'Original_Setup_File', 'LOG')}] -> [{copy_to_dir}]")
        #
        # shutil.copytree(os.path.join(copy_to_dir, "Original_Setup_File", "LoopScript"), copy_to_dir)
        # logger.info(f"copytree [{os.path.join(copy_to_dir, 'Original_Setup_File', 'LoopScript')}] -> [{copy_to_dir}]")
        #
        # shutil.copytree(os.path.join(copy_to_dir, "Original_Setup_File", "Capacity_Check"), copy_to_dir)
        # logger.info(f"copytree [{os.path.join(copy_to_dir, 'Original_Setup_File', 'Capacity_Check')}] -> [{copy_to_dir}]")

    if not Path(original_csv_path).exists():
        logger.warn(f"{original_csv_path} does not exist")
        return

    # コマンドライン引数で受け取ったcsvを開く
    # 명령줄 인수로 받은 CSV 열기
    # '\n'포함 안함
    read_csv = None
    if csv_type != -1:
        with open(original_csv_path, "r", errors="ignore") as csv:
            read_csv = csv.read().splitlines()
        logger.info(f"read [{original_csv_path}]")

    # 装置台数10台毎に複製される設定ファイルの場合
    # 장치 대수 10대마다 복제되는 설정 파일의 경우
    csv_line = []
    csv_header1 = None
    csv_header2 = None
    if csv_type == 0:

        j = 0
        csv_header1 = f"{read_csv[0]}\n"
        csv_header2 = f"{read_csv[1]}\n"
        list_idx = 2
        is_loop = True
        toolinfo_seperate_size = int(get_ini_value(config.config_ini, "LIPLUS", "LIPLUS_TOOL_INFO_SEPERATE_SIZE"))

        while is_loop:
            array_len = 0
            csv_line = []
            for _ in range(toolinfo_seperate_size):
                if list_idx < len(read_csv):
                    csv_line.append(f"{read_csv[list_idx]}\n")
                    list_idx += 1
                    array_len += 1
                else:
                    is_loop = False
                    break

            j += 1
            num_str = str(j)
            # new_dir_name = f"{dir_name}_{num_str}"
            setting_csv_name_change = f"{setting_csv_name.split('.')[0]}{num_str}.csv"

            # 폴더 생성
            # to_dir = Path(copy_to_dir, new_dir_name)
            # to_dir.mkdir(exist_ok=True)
            # logger.info(f"make dir [{to_dir.absolute()}]")

            # dir_path = Path(copy_to_dir, dir_name)
            # if new_dir_path.exists():
            #     rmtree(dir_path.absolute())
            #     logger.info(f"rmtree [{dir_path.absolute()}]")
            # else:
            #     dir_path.rename(new_dir_path)
            #     logger.info(f"rename [{dir_path.absolute()}] -> [{new_dir_path}]")

            # リネームしたフォルダに空のcsvファイルを生成
            # 이름이 바뀐 폴더에 빈 CSV 파일 생성
            new_csv_path = Path(copy_to_dir, setting_csv_name_change)
            if new_csv_path.exists():
                new_csv_path.unlink(missing_ok=True)
                logger.info(f"delete [{new_csv_path.absolute()}]")
            with open(new_csv_path, "a") as new_csv:
                # 空のcsvファイルにヘッダーを出力
                # 빈 CSV 파일에 헤더 출력
                new_csv.write(csv_header1)
                new_csv.write(csv_header2)
                # ヘッダーの下に装置情報を出力
                # 헤더 아래에 장치 정보 출력
                for ary_idx in range(array_len):
                    new_csv.write(csv_line[ary_idx])
            logger.info(f"write [{new_csv_path.absolute()}]")

    # 装置台数に依存しない設定ファイルの場合
    # 장치 수에 의존하지 않는 구성 파일의 경우
    elif csv_type == 1:
        start_idx = 1
        csv_header1 = f"{read_csv[0]}\n"
        if task_type == -1:
            csv_header2 = f"{read_csv[1]}\n"
            start_idx = 2

        for i in range(start_idx, len(read_csv)):
            csv_line.append(f"{read_csv[i]}\n")

        # フォルダをコピー
        # 폴더 복사
        # 폴더 복사는 불필요. 폴더 생성.
        # to_dir = Path(copy_to_dir, dir_name)
        # to_dir.mkdir(exist_ok=True)
        # logger.info(f"make dir [{to_dir.absolute()}]")
        # shutil.copytree(copy_from_dir, copy_to_dir)
        # logger.info(f"copytree [{copy_from_dir.absolute()}] -> [{copy_to_dir}]")

        # 空のcsvファイルを生成
        # 빈 CSV 파일 생성
        new_csv_path = Path(copy_to_dir, setting_csv_name)
        # 空のcsvファイルにヘッダーを出力
        # 빈 CSV 파일에 헤더 출력
        if new_csv_path.exists():
            new_csv_path.unlink(missing_ok=True)
            logger.info(f"delete [{new_csv_path.absolute()}]")
        with open(new_csv_path, "a") as new_csv:
            new_csv.write(csv_header1)
            if task_type == -1:
                new_csv.write(csv_header2)

            if len(csv_line) > 0:
                for i in range(len(csv_line)):
                    new_csv.write(csv_line[i])
        logger.info(f"write [{new_csv_path.absolute()}]")


def get_csv(original_csv_name, temp_csv_name):
    # コマンドライン引数で受け取ったcsvを開く
    # 명령줄 인수로 받은 CSV 열기
    # '\n'포함안함
    read_line = []
    csv_header = []
    csv_line = []
    start_idx = 2
    tool_name_list = []

    with open(original_csv_name, "r") as f:
        read_line = f.read().splitlines()

    if len(read_line) > 2:
        csv_header.append(read_line[0])
        csv_header.append(read_line[1])

    for i in range(start_idx, len(read_line)):
        csv_line.append(read_line[i])

    if len(csv_line) > 0:
        for i in range(len(csv_line)):
            is_write_line = True
            csv_split = csv_line[i].split(",")
            tool_name = csv_split[0]
            tool_id = csv_split[1]

            if tool_id != 1:
                # 従来機の場合、同じ装置を重複して設定するのを防ぐ(Com/ErrとRTlogで同じ装置を登録しているため)
                # 기존 기기의 경우 동일한 장치를 중복 설정하는 것을 방지(Com / Err과 RTlog에서 동일한 장치를 등록했기 때문에)
                for j in range(len(tool_name_list)):
                    if tool_name == tool_name_list:
                        is_write_line = False
                        break
                tool_name_list.append(tool_name)

            if is_write_line:
                with open(temp_csv_name, "a") as f:
                    f.write(f"{tool_name}\n")

def convCRLFtoLF(target_file):
    line = []

    with open(target_file, "r", errors="ignore") as f:
        line = f.read().splitlines()

    target = Path(target_file)
    write_xml = Path(target.parent, "TmpXml.xml")
    with open(write_xml.absolute(), "w") as f:
        for tmp_line in line:
            f.write(f"{tmp_line}\n")

    target.unlink(missing_ok=True)
    write_xml.rename(target.absolute())

def fdt_toolinfo_gen(tool_name, temp_xml_name):
    line = '  <Target>\n' \
           f'   <Property name="ImmutableId" value="{tool_name}" />\n' \
           '  </Target>\n'
    with open(temp_xml_name, "a", errors="ignore") as f:
        f.write(line)

def fdt_properties_gen(tool_name, temp_txt_name):
    line = f"java.util.logging.FileHandler.pattern = C:/ADS/fdt_batch/fcs/log/fcslogcollect.{tool_name}.log.%g\n"
    with open(temp_txt_name, "a", errors="ignore") as f:
        f.write(line)

# def liplus_mklink(type, tmp_dir_path, liplus_path):
#     shutil.copytree(tmp_dir_path, liplus_path)
#     rmtree(tmp_dir_path)
#
#     i = 1
#     for f in os.listdir(liplus_path):
#         file = Path(liplus_path, f)
#         if file.suffix == ".bat":
#             file_path = Path(liplus_path, f)
#             mklink(file_path.absolute(), f"Liplus_Loop_{type}_{i}.lnk", liplus_path)
#             i += 1

def make_fdt():
    # REM fdt_batchのconfファイルを生成する
    # fdt_batch의 conf 파일 생성
    fdt_conf_dir = Path(config.CSV_REAL_DIR, "fdt_batch", "fcs", "conf")
    fdt_toolinfo_csv = Path(config.CSV_ORIGINAL_DIR, "fdt_batch_ToolINfo.csv")
    temp_csv = Path(config.CSV_ORIGINAL_DIR, "TempToolName.csv")
    temp_xml = Path(config.CSV_ORIGINAL_DIR, "fdt_conf_tmp", "TempToolNameConf.xml")
    header_conf = Path(config.CSV_ORIGINAL_DIR, "FCC_Header.xml")
    footer_conf = Path(config.CSV_ORIGINAL_DIR, "FCC_Footer.xml")
    conf_xml = Path(config.CSV_ORIGINAL_DIR, "module", "fdt_conf_tmp", "tmp_conf", "FileCollectConfig.xml")

    get_csv(fdt_toolinfo_csv, temp_csv)

    # REM 抽出してTempCsvに格納した装置名を1つずつ渡していく
    # 추출하여 TempCsv에 저장된 장치 이름을 하나씩 전달합니다.
    tool_name_list = []
    with open(temp_csv, "r", errors="ignore") as f:
        tool_name_list = f.read().splitlines()
    for i in range(len(tool_name_list)):
        fdt_toolinfo_gen(tool_name_list[i], temp_xml)

    # 生成したファイルにHeaderとFooterを結合する
    # 생성된 파일에 Header와 Footer를 결합
    # 複数ファイルを結合し1つのファイルにする
    # 여러 파일을 결합하여 하나의 파일로 만듭니다.
    with open(conf_xml, "w", errors="ignore") as conf, \
            open(header_conf, "r", errors="ignore") as header, \
            open(temp_xml, "r", errors="ignore") as tmp, \
            open(footer_conf, "r", errors="ignore") as footer:
        conf.write(header.read())
        conf.write(tmp.read())
        conf.write(footer.read())

    # 指定したディレクトリにあるファイルの改行文字をCRLFからLFに変える
    # 지정된 디렉토리에 있는 파일의 개행 문자를 CRLF에서 LF로 변경
    convCRLFtoLF(conf_xml.absolute())

    # ConfXmlをftd_bacthへ移動する
    # ConfXml을 ftd_bacth로 이동
    fdt_conf_dir.mkdir(exist_ok=True)
    try:
        shutil.move(conf_xml, Path(fdt_conf_dir, conf_xml.name))
    except Exception as e:
        logger.warn(e)

    # fdt_batchのpropertieファイルを生成する
    # fdt_batch의 property 파일 생성
    temp_properties_dir = Path(config.CSV_ORIGINAL_DIR, "module", "fdt_properties_tmp", "tmp_Properties")
    temp_properties_dir.mkdir(exist_ok=True)
    header_properties = Path(config.CSV_ORIGINAL_DIR, "module", "fdt_properties_tmp",
                             "ToolName_Properties_Footer.txt")
    footer_properties = Path(config.CSV_ORIGINAL_DIR, "module", "fdt_properties_tmp",
                             "ToolName_Properties_Footer.txt")
    for i in range(len(tool_name_list)):
        temp_properties_file = Path(config.CSV_ORIGINAL_DIR, "module", "fdt_properties_tmp",
                                    f"{tool_name_list[i]}_temp.txt")
        fdt_properties_gen(tool_name_list[i], temp_properties_file)

        temp_txt_name = f"{temp_properties_dir}{tool_name_list[i]}.logcollect.logging.properties"
        with open(temp_txt_name, "a", errors="ignore") as fw, \
                open(header_properties, "r", errors="ignore") as hr, \
                open(temp_properties_file, "r", errors="ignore") as tr, \
                open(footer_properties, "r", errors="ignore") as fr:
            fw.write(hr.read())
            fw.write(tr.read())
            fw.write(fr.read())
        temp_properties_file.unlink(missing_ok=True)

    # Propertieファイルをfdt_batchへ移動する
    # Properties 파일을 fdt_batch로 이동
    shutil.copytree(temp_properties_dir.absolute(), fdt_conf_dir.absolute(), dirs_exist_ok=True)

    # tempファイルを削除
    # temp 파일 삭제
    temp_csv.unlink(missing_ok=True)
    temp_xml.unlink(missing_ok=True)
    rmtree(temp_properties_dir.absolute())

# def make_liplus_shortcut(current_dir, target_dir):
#     # Liplus_Loop_Get/Transfer ショートカット設定
#     # Liplus_Loop_Get/Transfer 바로 가기 설정
#     # オンデマンド/アップロード機能用フォルダ
#     # 온디맨드/업로드 기능용 폴더
#     liplus_loop_get_path = Path(target_dir, "Liplus_LoopScript_Get")
#     liplus_loop_transfer_path = Path(target_dir, "Liplus_LoopScript_Transfer")
#     liplus_loop_get_tmp_dir = Path(target_dir, "Liplus_LoopScript_Get")
#     liplus_loop_transfer_tmp_dir = Path(target_dir, "Liplus_LoopScript_Transfer")
#
#     # liplus_mklink("Get", liplus_loop_get_tmp_dir.absolute(), liplus_loop_get_path.absolute())
#     # liplus_mklink("Transfer", liplus_loop_transfer_tmp_dir.absolute(), liplus_loop_transfer_path.absolute())


# /ADS/Setup_CSV.bat
def setup_csv():

    # REM 各ディレクトリ定義
    # 각 디렉토리 정의
    current_dir = Path(config.CONFIG_DIR)
    target_dir = Path(config.CURRENT_DIR)
    original_csv = Path(config.CSV_ORIGINAL_DIR)
    original_setup_file_dir = Path(current_dir.absolute(), "Original_Setup_File")
    old_setup_file_dir = Path(current_dir.absolute(), "Old_Setup_File")
    # REM Old_Setup_Fileの中に作るフォルダの名前が一意になるようにする
    # Old_Setup_File 안에 만들 폴더의 이름이 고유하게 만들기
    old_dir_name = Path(old_setup_file_dir, f"Old_Setup_File-{datetime.datetime.now().strftime(util.time_util.TIME_FORMAT_4)}")

    # REM ショートカットを削除visual studio debug batch file
    # 바로가기 삭제
    dellink(current_dir)

    # REM 管理者として実行
    # 관리자로 실행
    # 필요한가...
    # for /f "tokens=3 delims=\ " %%i in ('whoami /groups^|find "Mandatory"') do set LEVEL=%%i
    # If NOT "%LEVEL%" == "High" (
    # powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -Command "Start-Process %~f0 -Verb runas"
    # exit
    # )

    # REM 既にフォルダが存在する場合はOLDへ移動
    # 이미 폴더가 있으면 OLD로 이동
    if target_dir.exists():
        # REM 古いセットアップファイルを保持しておくためのフォルダを生成する
        # 이전 설치 파일을 보관할 폴더 생성
        os.makedirs(old_dir_name.absolute(), exist_ok=True)
        logger.info(f"make dir [{old_dir_name.absolute()}]")

        original_target = target_dir.absolute()
        target_dir.rename(os.path.join(old_dir_name, target_dir.name))
        logger.info(f"move [{original_target} -> {os.path.join(old_dir_name, target_dir.name)}]")

        # for f in target_dir.iterdir():
        #     old_dir_name_path = Path(old_dir_name, f)
        #     if old_dir_name_path.exists():
        #         old_dir_name_path.unlink(missing_ok=True)
        #         logger.info(f"delete [{old_dir_name_path.absolute()}]")
        #     try:
        #         shutil.move(Path(target_dir.absolute(), f), old_dir_name_path.absolute())
        #         logger.info(f"move [{target_dir.absolute()}] -> [{old_dir_name_path.absolute()}]")
        #         shutil.copytree(target_dir.absolute(), old_dir_name.absolute())
        #         logger.info(f"copytree [{target_dir.absolute()}] -> [{old_dir_name.absolute()}]")
        #     except Exception as e:
        #         logger.error(e)
        #
        # rmtree(target_dir.absolute())
    
    # REM ADSセットアップスクリプトを展開する専用のフォルダを作成
    # ADS 설치 스크립트를 배포하는 전용 폴더 만들기
    target_dir = Path(config.CURRENT_DIR)
    target_dir.mkdir(exist_ok=True)
    logger.info(f"make dir [{target_dir.absolute()}]")

    # REM 設定ファイルを参照しセットアップスクリプトの配置を行う
    # 구성 파일을 찾아 설치 스크립트 배치
    copy_csv(os.path.join(original_csv.absolute(), "Liplus_batch_LiplusToolInfo.csv"), current_dir)
    copy_csv(os.path.join(original_csv.absolute(), "CollectRequestFileUpload_UploadInfo.csv"), current_dir)
    copy_csv(os.path.join(original_csv.absolute(), "OnDemandCollectDownload_DownloadInfo.csv"), current_dir)
    copy_csv(os.path.join(original_csv.absolute(), "fdt_batch_ToolInfo.csv"), current_dir)
    copy_csv(os.path.join(original_csv.absolute(), "UploadBatch_UpToolInfo.csv"), current_dir)
    copy_csv("else_file", current_dir)

    # 2要素認証用設定ファイルの配置を行う
    # 2요소 인증용 설정 파일의 배치를 실시한다
    securityinfo = Path(config.SECURITYINFO_PATH)
    if securityinfo.exists():
        to_secu = Path(target_dir.absolute(), "csv", securityinfo.name)
        shutil.copy(securityinfo.absolute(), to_secu.absolute())
        logger.info(f"copy [{securityinfo.absolute()}] -> [{to_secu.absolute()}]")

    # 바로가기 만들필요 없을듯?
    # mklink("", "", "")

    # REM ####################################
    # REM fdt_batch対応
    # REM ####################################
    # fdt_batch 대응
    # shlee todo FDT. 나중에 확인하기
    # make_fdt()

    # ############## Liplus Loop Batch 残り処理 ###################
    # ############## Liplus Loop Batch 나머지 처리 ####################
    # 바로가기 만들필요 없을듯?
    # make_liplus_shortcut(current_dir, target_dir)

    # copy python source
    original_source = Path(config.ORIGINAL_SOURCE_DIR)
    to_source = Path(config.CURRENT_DIR, original_source.name)
    shutil.copytree(original_source.absolute(), to_source.absolute())

    fs_log = Path(target_dir.absolute(), "FSLOG")
    ondemand = Path(target_dir.absolute(), "ondemand")

    fs_log.mkdir(exist_ok=True)
    logger.info(f"make dir [{fs_log.absolute()}]")
    ondemand.mkdir(exist_ok=True)
    logger.info(f"make dir [{ondemand.absolute()}]")

if __name__ == '__main__':

    log_path = Path(config.FILE_LOG_SETUP_CSV_PATH)

    if not log_path.parent.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = log.TimedLogger(config.PROC_NAME_SETUP_CSV, log.Setting(config.FILE_LOG_SETUP_CSV_PATH))

    logger.info("--------------------START SETUP CSV--------------------")
    try:
        setup_csv()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.warn(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")
    logger.info("---------------------END SETUP CSV---------------------")
