import pickle


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
