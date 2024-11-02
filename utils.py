import pickle
import re
import os

import quickstart_googledrive
from upload2DB import DatabaseUploader
from authentic_file.config import DB_URL

# 以下为使用GoogleDrive 进行读取文件的函数
# def get_total_excel(thermo_flag, photo_flag):
#     if not thermo_flag and not photo_flag:
#         total_pkl = os.path.join(".", "total_excel", "total.pkl")
#         if not os.path.exists(total_pkl):
#             download_folder_contents(dir_dict["total_excel"], os.path.dirname(total_pkl))
#         with open(total_pkl, 'rb') as file:
#             df_total = pickle.load(file)
#         return df_total
#     elif photo_flag:
#         total_pkl = os.path.join(".", "total_pickle_photocatalysis", "photo_excel.pkl")
#         if not os.path.exists(total_pkl):
#             download_folder_contents(dir_dict["total_pickle_photocatalysis"], os.path.dirname(total_pkl))
#         with open(total_pkl, 'rb') as file:
#             df_total = pickle.load(file)
#         return df_total
#     elif thermo_flag:
#         total_pkl = os.path.join(".", "total_pickle_thermocatalysis", "thermo_excel.pkl")
#         if not os.path.exists(total_pkl):
#             download_folder_contents(dir_dict["total_pickle_thermocatalysis"], os.path.dirname(total_pkl))
#         with open(total_pkl, 'rb') as file:
#             df_total = pickle.load(file)
#         return df_total


def get_total_excel(thermo_flag, photo_flag):
    if not thermo_flag and not photo_flag:
        total_pkl = "./total_excel/total.pkl"
        with open(total_pkl, 'rb') as file:
            df_total = pickle.load(file)
        return df_total
    elif photo_flag:
        total_pkl = "./total_pickle_photocatalysis/photo_excel.pkl"
        with open(total_pkl, 'rb') as file:
            df_total = pickle.load(file)
        return df_total
    elif thermo_flag:
        total_pkl = "./total_pickle_thermocatalysis/thermo_excel.pkl"
        with open(total_pkl, 'rb') as file:
            df_total = pickle.load(file)
        return df_total


def save_files(uploaded_file, save_path):
    with open(save_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

"""
以下为检查上传的文件类型的通用函数
"""


def is_INCAR(file):
    try:
        lines = file.read().decode('utf-8').splitlines()
        file.seek(0)
        # 检查是否存在有效的参数行
        return any(line.strip() and '=' in line for line in lines)
    except Exception as e:
        print(f"Error reading INCAR file: {e}")
        return False


def is_KPOINTS(file):
    try:
        lines = file.read().decode('utf-8').splitlines()
        file.seek(0)
        # 检查文件是否有足够的行
        if len(lines) < 5:
            return False

        # 第一个有效行应为 K 点数量（不应是注释或空行）
        kpoints_count_line = lines[1].strip()
        if not kpoints_count_line.isdigit():
            return False

        # 检查 K 点选择方法
        kpoint_selection = lines[2].strip()
        if kpoint_selection not in ["Gamma", "Monkhorst", "Automatically generated", "Other"]:
            return False

        # 检查 K 点网格
        kpoints_grid = lines[3].strip().split()
        if len(kpoints_grid) != 3 or not all(x.isdigit() for x in kpoints_grid):
            return False

        # 可以继续进一步检查 K 点坐标，视需要而定

        return True  # 文件有效
    except Exception as e:
        print(f"Error reading KPOINTS file: {e}")
        return False


def is_CONTCAR(file):
    try:
        lines = file.read().decode('utf-8').splitlines()
        file.seek(0)

        # 文件行数至少应该多于8行
        if len(lines) < 8:
            return False

        # 第二行应为浮点数（缩放因子）
        try:
            float(lines[1].strip())
        except ValueError:
            return False

        # 第三到第五行应该包含3个浮点数
        for i in range(2, 5):
            if len(lines[i].split()) != 3:
                return False
            try:
                [float(x) for x in lines[i].split()]
            except ValueError:
                return False

        # 第六行应为元素符号，通常是大写字母或元素符号
        if not all(x.isalpha() for x in lines[5].split()):
            return False

        # 第七行应为原子数量的整数列表
        try:
            [int(x) for x in lines[6].split()]
        except ValueError:
            return False

        return True
    except Exception as e:
        print(f"Error reading file: {e}")
        return False


def is_CIF(file):
    """
    严格检测文件对象是否为标准的 CIF 文件。

    通过检查文件结构、关键字和符合 IUCr 标准的格式来确保检测的准确性。

    :param file: 已打开的文件对象,二进制字节
    :return: 如果是标准 CIF 文件返回 True，否则返回 False
    """
    # 定义 CIF 文件常见的正则表达式
    cif_data_block_pattern = re.compile(r"^data_.*")  # CIF 文件必须以 data_ 开头
    cif_key_value_pattern = re.compile(r"^_\w+[\s\S]*")  # CIF 中的 key-value 格式，key 以 _ 开头
    cif_loop_pattern = re.compile(r"^loop_")  # CIF 中的循环数据
    try:
        lines = file.read().decode('utf-8').splitlines()
    except UnicodeDecodeError as e:
        print(e)
        return False
    file.seek(0)

    try:
        data_block_found = False
        valid_lines = 0  # 有效的 CIF 行计数

        # 逐行读取文件对象
        for line in lines:
            line = line.strip()

            # 检查是否包含 data_ 数据块
            if cif_data_block_pattern.match(line):
                data_block_found = True
                # print("data_block_found")

            # 检查 key-value 格式或者 loop_
            if cif_key_value_pattern.match(line) or cif_loop_pattern.match(line):
                valid_lines += 1

        # 判断文件是否符合 CIF 文件的基本格式
        if data_block_found and valid_lines > 0:
            return True  # 满足所有 CIF 标准
        else:
            return False  # 不满足 CIF 标准

    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return False


def is_XYZ(file):
    try:
        # 读取文件内容并将其拆分为多行
        lines = file.read().decode('utf-8').splitlines()
        file.seek(0)  # 重置文件指针，以便其他地方继续读取文件

        # 文件行数至少应为3行（原子数量、注释行、至少一个原子及其坐标）
        if len(lines) < 3:
            return False

        # 第1行应为正整数，表示原子数量
        try:
            atom_count = int(lines[0].strip())
            if atom_count <= 0:
                return False
        except ValueError:
            return False

        # 第2行是注释，可以是任意内容，不需要检测

        # 从第3行开始，每一行应包含一个原子符号和三个坐标
        for i in range(2, len(lines)):
            parts = lines[i].split()

            # 检查行是否包含4个部分：元素符号 + 3个坐标值
            if len(parts) != 4:
                return False

            # 第一个部分应该是原子符号，检查是否为1个或2个字母
            atom_symbol = parts[0]
            if not (len(atom_symbol) == 1 and atom_symbol.isalpha() and atom_symbol.isupper()) and \
               not (len(atom_symbol) == 2 and atom_symbol[0].isupper() and atom_symbol[1].islower()):
                return False

            # 后面的三个部分应该是浮点数（原子坐标）
            try:
                [float(coord) for coord in parts[1:]]
            except ValueError:
                return False

        # 如果所有检查通过，返回 True
        return True

    except Exception as e:
        print(f"Error reading file: {e}")
        return False


def is_valid_doi(doi):
    """
    检查给定的 DOI 是否是合法格式。

    :param doi: 要检查的 DOI 字符串
    :return: 如果合法返回 None，不合法返回错误信息
    """
    # DOI 格式的正则表达式：10. 后跟数字、斜杠以及后缀
    doi_pattern = r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$"

    # 使用正则表达式进行匹配
    if re.match(doi_pattern, doi):
        return True  # 合法 DOI，返回 None
    else:
        return False


def get_formula_adsorbate(filename):
    name_without_extension = os.path.splitext(filename)[0]

    # 用下划线分割文件名
    parts = name_without_extension.split('_')

    # 提取 formula 和 adsorbate_dic 的逻辑
    if len(parts) == 3:
        # 如果包含三个部分，说明有 file_type, formula 和 adsorbate_dic
        file_type, formula, adsorbate = parts
    elif len(parts) == 2:
        # 如果只有两个部分，说明只有 file_type 和 formula，没有 adsorbate_dic
        file_type, formula = parts
        adsorbate = None  # 没有 adsorbate_dic
    else:
        raise ValueError

    return formula, adsorbate


def is_filename_valid(filename, file_type):
    # 去掉扩展名，获取文件名和扩展名
    name_without_extension, ext = os.path.splitext(filename)
    if file_type in ['INCAR', 'KPOINTS']:
        parts = name_without_extension.split('_')
        if len(parts) == 2 and parts[0] == file_type:
            return True
        else:
            return False
    # CONTCAR 文件没有扩展名，遵循 f"{file_type}_{formula}_{adsorbate_dic}" 的规则
    if file_type in ['CONTCAR']:
        parts = name_without_extension.split('_')
        if len(parts) == 3 and parts[0] == file_type:
            return True
        elif len(parts) == 2 and parts[0] == file_type:  # 没有 adsorbate_dic 的情况
            return True
        else:
            return False

    # CIF 和 XYZ 文件要遵循 f"{file_type}_{formula}_{adsorbate_dic}"，并且有扩展名
    elif file_type == 'CIF' or file_type == 'XYZ':
        if ext.lower() != f".{file_type.lower()}":  # 检查扩展名
            return False

        parts = name_without_extension.split('_')
        if len(parts) == 3 and parts[0] == file_type:
            return True
        elif len(parts) == 2 and parts[0] == file_type:  # 没有 adsorbate_dic 的情况
            return True
        else:
            return False

    # 如果文件类型不符合任何已知类型，则返回 False
    return False


def is_doi_name_match(doi_in, current_name, select_type, sheet_name):
    # 设置不同数据类型的 Excel 文件路径
    if select_type == "Experimental":
        pkl_path = "./computational_data/experimental_data.pkl"
        # if os.path.exists(pkl_path):
        #     df = pd.read_excel(pkl_path)
        if not os.path.exists(pkl_path):
            quickstart_googledrive.file_from_gdrive(quickstart_googledrive.dir_dict["computational_data"], "experimental_data.pkl",
                                                    quickstart_googledrive.init_drive_client(), pkl_path)
            raise FileNotFoundError
        total_dic = pickle.load(open(pkl_path, "rb"))
        df = total_dic[sheet_name]
    elif select_type == "Computational":
        pkl_path = "./computational_data/computational_data.pkl"
        if not os.path.exists(pkl_path):
            quickstart_googledrive.file_from_gdrive(quickstart_googledrive.dir_dict["computational_data"], "computational_data.pkl",
                                                    quickstart_googledrive.init_drive_client(), pkl_path)
            raise FileNotFoundError
        total_dic = pickle.load(open(pkl_path, "rb"))
        df = total_dic[sheet_name]
    elif isinstance(select_type, bool) :
        db_conn = DatabaseUploader(DB_URL)
        df = db_conn.get_doi_uploader(sheet_name)
    else:
        raise "Option out of range."

    # 检查是否存在指定 DOI
    if doi_in not in df["DOI"].values:
        return None

    # 获取对应 DOI 的 Uploader
    registered_name = df.loc[df["DOI"] == doi_in, "Uploader"].values[0]

    # 判断当前 name 是否匹配
    if registered_name == current_name:
        return None  # 匹配成功
    else:
        return f"Error: DOI {doi_in} was uploaded by others, not {current_name}."


# 文件夹对应的检查函数映射
check_functions = {
    'CONTCAR': is_CONTCAR,
    'CIF': is_CIF,
    'INCAR': is_INCAR,
    'KPOINTS': is_KPOINTS,
    'XYZ': is_XYZ
}


if __name__ == '__main__':
    print(is_filename_valid("CONTCAR", "CONTCAR_Co-Pc"))


