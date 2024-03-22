import datetime
import os.path
import shutil

import service.common.common_service as com
import config.app_config as config
import util.time_util as time_util

from service.common.common_service import xcopy_file_to_dir
from pathlib import Path

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

        file.unlink(missing_ok=True)

def mklink(link_path, link_name, work_dir):
    # shlee 시발 바로가기 어케만듬;;
    pass


# /ADS/module/Csv_Copy.vbs
def copy_csv(original_csv_path, base_dir):
    module_path = Path(base_dir, "module")
    setting_csv_name = ""
    dir_name = ""
    csv_type = 0
    task_type = 0
    copy_from_dir = None
    copy_to_dir = config.CSV_REAL_PATH

    if "Liplus_batch" in original_csv_path:
        copy_from_dir = Path(copy_to_dir, "Liplus_batch")
        dir_name = "Liplus_batch"
        setting_csv_name = "LiplusToolInfo.csv"
        csv_type = 0
        task_type = 0
    elif "Liplus_batch_recovery" in original_csv_path:
        copy_from_dir = Path(copy_to_dir, "Liplus_batch_recovery")
        dir_name = "Liplus_batch_recovery"
        setting_csv_name = "LiplusToolInfo.csv"
        csv_type = 0
        task_type = 1
    elif "CollectRequestFileUpload" in original_csv_path:
        copy_from_dir = Path(copy_to_dir, "CollectRequestFileUpload")
        dir_name = "CollectRequestFileUpload"
        setting_csv_name = "UploadInfo.csv"
        csv_type = 1
        task_type = 2
    elif "UploadBatch" in original_csv_path:
        copy_from_dir = Path(copy_to_dir, "UploadBatch")
        dir_name = "UploadBatch"
        setting_csv_name = "UploadInfo.csv"
        csv_type = 1
        task_type = 3
    elif "OnDemandCollectDownload" in original_csv_path:
        copy_from_dir = Path(copy_to_dir, "OnDemandCollectDownload")
        dir_name = "OnDemandCollectDownload"
        setting_csv_name = "DownloadInfo.csv"
        csv_type = 1
        task_type = 4
    elif "fdt_batch" in original_csv_path:
        copy_from_dir = Path(copy_to_dir, "fdt_batch")
        dir_name = "fdt_batch"
        setting_csv_name = "ToolInfo.csv"
        csv_type = 1
        task_type = -1
    elif "else_file" in original_csv_path:
        csv_type = -1

    copy_from_dir.mkdir(exist_ok=True)

    # 設定ファイルの存在しないScriptに関しては何もせずコピー
    # 설정 파일이 존재하지 않는 Script에 관해서는 아무것도하지 않고 복사
    if csv_type == -1:
        # CopyFSO.CopyFolder OriginalPath & "\Original_Setup_File" & "\AutoCC_Loop", CpToPath
        shutil.copytree(os.path.join(copy_to_dir, "Original_Setup_File", "AutoCC_Loop"), copy_to_dir)
        shutil.copytree(os.path.join(copy_to_dir, "Original_Setup_File", "Liplus_LOG"), copy_to_dir)
        shutil.copytree(os.path.join(copy_to_dir, "Original_Setup_File", "LOG"), copy_to_dir)
        shutil.copytree(os.path.join(copy_to_dir, "Original_Setup_File", "LoopScript"), copy_to_dir)
        shutil.copytree(os.path.join(copy_to_dir, "Original_Setup_File", "Capacity_Check"), copy_to_dir)

    # コマンドライン引数で受け取ったcsvを開く
    # 명령줄 인수로 받은 CSV 열기
    # '\n'포함 안함
    read_csv = None
    with open(original_csv_path, "r") as csv:
        read_csv = csv.read().splitlines()

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

        while is_loop:
            array_len = 0
            csv_line = [None] * 10
            for _ in range(10):
                if list_idx < len(read_csv):
                    csv_line.append(f"{read_csv[list_idx]}\n")
                    list_idx += 1
                    array_len += 1
                else:
                    is_loop = False

            j += 1
            num_str = str(j)
            new_dir_name = f"{dir_name}_{num_str}"

            # フォルダをコピー
            # 폴더 복사
            shutil.copytree(copy_from_dir, copy_to_dir)

            # フォルダをリネーム
            # 폴더 이름 바꾸기
            # if os.path.exists(os.path.join(copy_to_dir, new_dir_name)):
            new_dir_path = Path(copy_to_dir, new_dir_name)
            dir_path = Path(copy_to_dir, dir_name)
            if new_dir_path.exists():
                com.rmtree(dir_path.absolute())
            else:
                dir_path.rename(new_dir_path)

            # リネームしたフォルダに空のcsvファイルを生成
            # 이름이 바뀐 폴더에 빈 CSV 파일 생성
            new_csv_path = Path(copy_to_dir, new_dir_name, setting_csv_name)
            if new_csv_path.exists():
                new_csv_path.unlink(missing_ok=True)
            with open(new_csv_path, "a") as new_csv:
                # 空のcsvファイルにヘッダーを出力
                # 빈 CSV 파일에 헤더 출력
                new_csv.write(csv_header1)
                new_csv.write(csv_header2)
                # ヘッダーの下に装置情報を出力
                # 헤더 아래에 장치 정보 출력
                for ary_idx in range(array_len):
                    new_csv.write(csv_line[ary_idx])

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
        shutil.copytree(copy_from_dir, copy_to_dir)

        # 空のcsvファイルを生成
        # 빈 CSV 파일 생성
        new_csv_path = Path(copy_to_dir, dir_name, setting_csv_name)
        # 空のcsvファイルにヘッダーを出力
        # 빈 CSV 파일에 헤더 출력
        with open(new_csv_path, "a") as new_csv:
            new_csv.write(csv_header1)
            if task_type == -1:
                new_csv.write(csv_header2)

            if len(csv_line) > 0:
                for i in range(len(csv_line)):
                    new_csv.write(csv_line[i])


def get_csv(original_csv_name, temp_csv_name):
    # コマンドライン引数で受け取ったcsvを開く
    # 명령줄 인수로 받은 CSV 열기
    # '\n'포함안함
    read_line = []
    csv_header = []
    csv_line = []
    start_idx = 2
    is_write_line = True

    with open(original_csv_name, "r") as f:
        read_line = f.read().splitlines()

    if len(read_line) > 2:
        csv_header.append(read_line[0])
        csv_header.append(read_line[1])

    for i in range(start_idx, len(read_line)):
        csv_line.append(read_line[i])

    if len(csv_line) > 0:
        # 실제 vbs파일에선 안에서 루프를 도는데...이상함;;루프 돌 필요 없을듯..
        csv_split = csv_line[0].split(",")
        tool_name = csv_split[0]
        tool_id = csv_split[1]

        if tool_id != 1:
            # 従来機の場合、同じ装置を重複して設定するのを防ぐ(Com/ErrとRTlogで同じ装置を登録しているため)
            # 기존 기기의 경우 동일한 장치를 중복 설정하는 것을 방지(Com / Err과 RTlog에서 동일한 장치를 등록했기 때문에)
            if tool_name == "":
                is_write_line = False
        with open(temp_csv_name, "w") as f:
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

def liplus_mklink(type, tmp_dir_path, liplus_path):
    shutil.copytree(tmp_dir_path, liplus_path)
    com.rmtree(tmp_dir_path)

    i = 1
    for f in os.listdir(liplus_path):
        file = Path(liplus_path, f)
        if file.suffix == ".bat":
            file_path = Path(liplus_path, f)
            mklink(file_path.absolute(), f"Liplus_Loop_{type}_{i}.lnk", liplus_path)
            i += 1

# /ADS/Setup_CSV.bat
def setup_csv():

    # REM 各ディレクトリ定義
    # 각 디렉토리 정의
    current_dir = Path('/ADS/')
    target_dir = Path('/ADS/')
    original_csv = Path('/ADS/originalcsv')
    original_setup_file_dir = Path(current_dir, "Original_Setup_File")
    old_setup_file_dir = Path(current_dir, "Old_Setup_File")
    # REM Old_Setup_Fileの中に作るフォルダの名前が一意になるようにする
    # Old_Setup_File 안에 만들 폴더의 이름이 고유하게 만들기
    old_dir_name = Path(old_setup_file_dir, f"Old_Setup_File-{datetime.datetime.now().strftime(time_util.TIME_FORMAT_4)}")

    # REM ショートカットを削除
    # 바로가기 삭제
    if Path(current_dir, "module", "DelLink.bat").exists():
        dellink(current_dir)

    # REM ADSのセットアップスクリプトの一覧を格納する一時ファイル
    # ADS 설치 스크립트 목록을 저장하는 임시 파일
    script_temp = Path(current_dir, "FolderNameList.txt")
    if script_temp.exists():
        script_temp.unlink(missing_ok=True)

    # REM 管理者として実行
    # 관리자로 실행
    # 필요한가...
    # for /f "tokens=3 delims=\ " %%i in ('whoami /groups^|find "Mandatory"') do set LEVEL=%%i
    # If NOT "%LEVEL%" == "High" (
    # powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -Command "Start-Process %~f0 -Verb runas"
    # exit
    # )

    # REM 古いセットアップファイルを保持しておくためのフォルダを生成する
    # 이전 설치 파일을 보관할 폴더 생성
    old_dir_name.mkdir(exist_ok=True)

    # REM セットアップファイルの種類を取得する
    # 설치 파일 형식 얻기
    with open(script_temp, "a") as txt:
        for f in original_setup_file_dir.iterdir():
            txt.write(f"{f}\n")

    # REM 既にフォルダが存在する場合はOLDへ移動
    # 이미 폴더가 있으면 OLD로 이동
    if target_dir.exists():
        for f in target_dir.iterdir():
            old_dir_name_path = Path(old_dir_name, f)
            if old_dir_name_path.exists():
                old_dir_name_path.unlink(missing_ok=True)
            shutil.move(Path(target_dir.absolute(), f), old_dir_name_path)
            shutil.copytree(target_dir.absolute(), old_dir_name)
        com.rmtree(target_dir.absolute())
    # REM ADSセットアップスクリプトを展開する専用のフォルダを作成
    # ADS 설치 스크립트를 배포하는 전용 폴더 만들기
    target_dir.mkdir(exist_ok=True)

    # REM セットアップファイル名の入ったtxtを削除
    # 설치 파일 이름이 포함된 txt 삭제
    script_temp.unlink(missing_ok=True)

    # REM 設定ファイルを参照しセットアップスクリプトの配置を行う
    # 구성 파일을 찾아 설치 스크립트 배치
    copy_csv(os.path.join(original_csv, "Liplus_batch_LiplusToolInfo.csv"), current_dir)
    copy_csv(os.path.join(original_csv, "CollectRequestFileUpload_UploadInfo.csv"), current_dir)
    copy_csv(os.path.join(original_csv, "OnDemandCollectDownload_DownloadInfo.csv"), current_dir)
    copy_csv(os.path.join(original_csv, "fdt_batch_ToolInfo.csv"), current_dir)
    copy_csv(os.path.join(original_csv, "UploadBatch_UpToolInfo.csv"), current_dir)
    copy_csv("else_file", current_dir)

    # 2要素認証用設定ファイルの配置を行う
    # 2요소 인증용 설정 파일의 배치를 실시한다
    securityinfo = Path(config.SECURITYINFO_PATH)
    if securityinfo.exists():
        shutil.copy(securityinfo, Path(target_dir, securityinfo.name))

    # REM ############## Liplus Loop Batch ###################
    # shlee todo mklink
    mklink("", "", "")

    # REM ####################################
    # REM fdt_batch対応
    # REM ####################################
    # fdt_batch 대응
    # REM fdt_batchのconfファイルを生成する
    # fdt_batch의 conf 파일 생성
    fdt_conf_dir = Path(config.CSV_REAL_PATH, "fdt_batch", "fcs", "conf")
    fdt_toolinfo_csv = Path(config.CSV_ORIGINAL_PATH, "fdt_batch_ToolINfo.csv")
    temp_csv = Path(config.CSV_ORIGINAL_PATH, "module", "TempToolName.csv")
    temp_xml = Path(config.CSV_ORIGINAL_PATH, "module", "fdt_conf_tmp", "TempToolNameConf.xml")
    header_conf = Path(config.CSV_ORIGINAL_PATH, "module", "fdt_conf_tmp", "FCC_Header.xml")
    footer_conf = Path(config.CSV_ORIGINAL_PATH, "module", "fdt_conf_tmp", "FCC_Footer.xml")
    conf_xml = Path(config.CSV_ORIGINAL_PATH, "module", "fdt_conf_tmp", "tmp_conf", "FileCollectConfig.xml")

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
    convCRLFtoLF(conf_xml)

    # ConfXmlをftd_bacthへ移動する
    # ConfXml을 ftd_bacth로 이동
    fdt_conf_dir.mkdir(exist_ok=True)
    shutil.move(conf_xml, Path(fdt_conf_dir, conf_xml.name))

    # fdt_batchのpropertieファイルを生成する
    # fdt_batch의 property 파일 생성
    temp_properties_dir = Path(config.CSV_ORIGINAL_PATH, "module", "fdt_properties_tmp", "tmp_Properties")
    temp_properties_dir.mkdir(exist_ok=True)
    header_properties = Path(config.CSV_ORIGINAL_PATH, "module", "fdt_properties_tmp",
                                     "ToolName_Properties_Footer.txt")
    footer_properties = Path(config.CSV_ORIGINAL_PATH, "module", "fdt_properties_tmp",
                                     "ToolName_Properties_Footer.txt")
    for i in range(len(tool_name_list)):
        temp_properties_file = Path(config.CSV_ORIGINAL_PATH, "module", "fdt_properties_tmp",
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
    com.rmtree(temp_properties_dir.absolute())

    # オンデマンド/アップロード機能用フォルダ
    # 온디맨드/업로드 기능용 폴더
    liplus_loop_get_path = Path(target_dir, "Liplus_LoopScript_Get")
    liplus_loop_transfer_path = Path(target_dir, "Liplus_LoopScript_Transfer")
    liplus_loop_get_tmp_dir = Path(target_dir, "Liplus_LoopScript_Get")
    liplus_loop_transfer_tmp_dir = Path(target_dir, "Liplus_LoopScript_Transfer")

    liplus_mklink("Get", liplus_loop_get_tmp_dir.absolute(), liplus_loop_get_path.absolute())
    liplus_mklink("Transfer", liplus_loop_transfer_tmp_dir.absolute(), liplus_loop_transfer_path.absolute())

    fs_log = Path(current_dir, "FSLOG")
    ondemand = Path(current_dir, "ondemand")

    if not fs_log.exists():
        fs_log.mkdir()
    if not ondemand.exists():
        ondemand.mkdir()

if __name__ == '__main__':
    setup_csv()
