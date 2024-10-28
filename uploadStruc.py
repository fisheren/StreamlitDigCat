import os
import pandas as pd
import pickle

import quickstart_googledrive
from utils import is_INCAR, is_KPOINTS, is_CONTCAR, check_functions
from quickstart_googledrive import upload_or_replace_file_by_file, dir_dict, download_folder_contents, init_drive_client


# 上传数据函数，处理实验数据和纯计算数据
def upload_struc_data(df, formula, doi, uploader_name, adsorbate_type=None, adsorbate_energy=None):
    """
    将数据合并至df中，并上传到GoogleDrive
    :param df:
    :param formula:
    :param doi:
    :param uploader_name:
    :param adsorbate_type:
    :param adsorbate_energy:
    :return: None or Error info
    """

    # 查找匹配的 DOI 和 Formula 的行
    condition = (df["DOI"] == doi) & (df["Formula"] == formula)

    if condition.any():  # 如果找到匹配的行
        # 如果没有吸附物，则上传的是基底数据
        if adsorbate_type is None:
            return df
        # 检查是否有该 adsorbate_type 列
        if adsorbate_type not in df.columns:
            df[adsorbate_type] = None  # 如果没有该列，添加此列

        # 更新对应行的吸附物能量和上传者名字
        df.loc[condition, adsorbate_type] = adsorbate_energy
        df.loc[condition, "Uploader"] = uploader_name  # 更新上传者名字
    else:

        # 如果没有找到匹配行，则添加一行
        new_data = {
            "Formula": formula,
            "DOI": doi,
            "Uploader": uploader_name  # 添加上传者名字
        }
        if adsorbate_type is not None:
            new_data[adsorbate_type] = adsorbate_energy
        df = pd.concat([df, pd.DataFrame(new_data, index=[0])], ignore_index=True)

    # 保存更新后的文件
    return df


def upload_struc_file(file_type, doi, file, formula, adsorbate_name=None):
    # 检查文件是否提供
    if file is None:
        return "No file provided."

    # 根据文件类型进行检查
    check_function = check_functions[file_type]
    if check_function:
        if not check_function(file):
            return f"Not A {file_type} file. "

    # 检查化学式是否提供
    if formula is None:
        return "No formula provided."

    # 构建安全的 DOI 文件夹路径
    doi = doi.replace("/", "-")

    # 构建文件夹路径
    _fp = f"./computational_data/{file_type}/{doi}/"

    # 如果路径不存在，创建目录
    if not os.path.exists(_fp):
        os.makedirs(_fp, exist_ok=True)

    file_type_dic = {
        "CIF": ".cif",
        "CONTCAR": "",
        "XYZ": ".xyz",
    }
    if adsorbate_name:
        file_name = f"{file_type}_{formula}_{adsorbate_name}{file_type_dic[file_type]}"
    else:
        file_name = f"{file_type}_{formula}{file_type_dic[file_type]}"

    # 将文件写入目标文件夹
    file_path = os.path.join(_fp, file_name)

    service = init_drive_client()
    file_type_folder_id = dir_dict[file_type]
    doi_folder_id = quickstart_googledrive.create_or_get_subfolder_id(service, doi, file_type_folder_id)
    upload_or_replace_file_by_file(file_name, file, "text/plain", doi_folder_id, service)
    print(f"File {file_name} has been uploaded successfully to {file_path}")
    return None


def upload_INCAR_KPOINTS_file(doi, file, formula, drive_service=quickstart_googledrive.init_drive_client()):
    # 判断文件类型
    if is_INCAR(file):
        file_type = "INCAR"
        mimetype = 'text/plain'  # INCAR 文件的 MIME 类型
    elif is_KPOINTS(file):
        file_type = "KPOINTS"
        mimetype = 'text/plain'
    else:
        return f"Invalid file type."
    doi = doi.replace("/", "-")

    # 生成文件名
    file_name = f"{file_type}_{formula}"
    file_type_folder_id = dir_dict[file_type]
    doi_folder_id = quickstart_googledrive.create_or_get_subfolder_id(drive_service, doi, file_type_folder_id)
    # 调用 upload_or_replace_file 上传或替换文件
    try:
        file_id = quickstart_googledrive.upload_or_replace_file_by_file(file_name, file, mimetype, doi_folder_id)
    except Exception as e:
        return f"Failed to upload file: {str(e)}"
    if file_id:
        return None  # 上传成功，返回 None


def is_doi_name_match(doi_in, current_name, select_type, sheet_name):
    # 设置不同数据类型的 Excel 文件路径
    if select_type == "Experimental":
        excel_path = "./computational_data/experimental_data.pkl"
        # if os.path.exists(excel_path):
        #     df = pd.read_excel(excel_path)
        if not os.path.exists(excel_path):
            quickstart_googledrive.file_from_gdrive(dir_dict["computational_data"], "experimental_data.pkl",
                                                    init_drive_client(), excel_path)
        total_dic = pickle.load(open(excel_path, "rb"))
        df = total_dic[sheet_name]
    elif (select_type == "Computational" or
          select_type == "Computational Structures(including adsorption free energies)"):
        excel_path = "./computational_data/computational_data.pkl"
        if not os.path.exists(excel_path):
            quickstart_googledrive.file_from_gdrive(dir_dict["computational_data"], "computational_data.pkl",
                                                    init_drive_client(), excel_path)
        total_dic = pickle.load(open(excel_path, "rb"))
        df = total_dic[sheet_name]
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
