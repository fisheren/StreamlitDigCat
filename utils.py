import pickle
import re



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


"""
以下为检查上传的文件类型的通用函数
"""


def is_incar(file):
    try:
        lines = file.read().decode('utf-8').splitlines()
        file.seek(0)
        # 检查是否存在有效的参数行
        return any(line.strip() and '=' in line for line in lines)
    except Exception as e:
        print(f"Error reading INCAR file: {e}")
        return False


def is_kpoints(file):
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


def is_contcar(file):
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


def is_cif(file):
    try:
        # 读取文件内容并将其拆分为多行
        lines = file.read().decode('utf-8').splitlines()
        file.seek(0)  # 重置文件指针，以便其他地方读取文件

        # CIF 文件应该至少包含一个 data_ 块（即以 data_ 开头的行）
        if not any(line.startswith("data_") for line in lines):
            return False

        # 检查是否存在至少一个以 _ 开头的关键字（key-value 对）
        if not any(line.startswith("_") for line in lines):
            return False

        # 检查是否包含至少一行数据循环的标记 "loop_"
        if not any(line.startswith("loop_") for line in lines):
            return False

        # 进一步检查关键字和值的格式，如 _key value
        for line in lines:
            line = line.strip()

            # 如果是以 _ 开头的关键字行，检查是否有对应的值
            if line.startswith("_"):
                # 拆分关键字和值，确保至少有两个部分
                parts = line.split()
                if len(parts) < 2:
                    return False

                # 可以根据需要进一步检查关键字的合法性和格式，例如:
                # if not re.match(r"^_\w+$", parts[0]):
                #     return False

        # 如果通过了所有检查，返回 True
        return True

    except Exception as e:
        print(f"Error reading file: {e}")
        return False


def is_xyz(file):
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





# 文件夹对应的检查函数映射
check_functions = {
    'CONTCAR': is_contcar,
    'CIF': is_cif,
    'INCAR': is_incar,
    'KPOINTS': is_kpoints,
    'XYZ': is_xyz
}

