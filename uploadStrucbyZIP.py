"""
本代码为解压zip文件并进行核对的方法
"""

import os
import zipfile
from fileinput import filename
from collections import defaultdict
from typing import List, Dict

import pandas as pd
import shutil
import pickle

from columns import adsorbate_dic
from utils import check_functions

import quickstart_googledrive
import utils
import uploadStruc

valid_folders = ['CONTCAR', 'CIF', 'INCAR', 'KPOINTS', 'XYZ']
valid_files = ['computational_data.xlsx', 'readme.txt', '~$computational_data.xlsx']


def load_pkl_data(pkl_file_path):
    """从指定路径加载或初始化一个空的DataFrame"""
    if os.path.exists(pkl_file_path):
        with open(pkl_file_path, 'rb') as f:
            pkl_data = pickle.load(f)
    else:
        raise FileNotFoundError
    return pkl_data


def save_pkl_data(pkl_file_path, data):
    """将更新后的数据保存到pkl文件"""
    with open(pkl_file_path, 'wb') as file:
        pickle.dump(data, file)


def check_folder_content(folder_path):
    # 获取文件夹中的所有内容
    folder_content = os.listdir(folder_path)

    # 分开文件和文件夹
    actual_folders = [item for item in folder_content
                      if os.path.isdir(os.path.join(folder_path, item))
                      and not item.startswith(('~', '.'))]  # 跳过~和.开头的文件夹

    actual_files = [item for item in folder_content
                    if os.path.isfile(os.path.join(folder_path, item))
                    and not item.startswith(('~', '.'))]  # 跳过~和.开头的文件

    # 检查文件夹是否全部合规
    for folder in actual_folders:
        if folder not in valid_folders:
            print(f"非法文件夹：{folder}")
            return False

    # 检查文件是否全部合规
    for file in actual_files:
        if file not in valid_files:
            print(f"非法文件：{file}")
            return False

    # 如果全部合规，返回 True
    return True


def check_subfolders_and_files(output_dir, valid_df: pd.DataFrame, sheet_name):
    # 遍历 output_dir 中的文件和文件夹
    valid_formula = valid_df['Formula'].unique()
    valid_df["DOI"] = valid_df['DOI'].apply(lambda x: x.replace('/', '-'))
    valid_dois: pd.Series = valid_df['DOI']
    get_formulas = []
    adsorbates = []
    checked_files = []
    infos: dict[str, list[str]] = {}
    doi_errs: list[str] = [f"You upload {valid_dois.unique()}"]
    formula_errs = []
    filename_errs = []
    file_type_errs = []

    for file_type_folder in os.listdir(output_dir):
        folder_path = os.path.join(output_dir, file_type_folder)

        # 只处理在 valid_folders 列表中的文件夹
        if file_type_folder in valid_folders and os.path.isdir(folder_path):
            print(f"正在检查文件夹: {file_type_folder}")

            # 遍历该文件夹中的子文件夹（例如，DOI 命名的子文件夹）
            doi_folders = [fn for fn in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, fn))]
            if doi_folders != valid_dois.unique().tolist():
                doi_errs.append(f"Got {doi_folders} in {file_type_folder}")

            for doi_folder in doi_folders:
                doi_folder = doi_folder.replace(':', '-')
                doi_folder_path = os.path.join(folder_path, doi_folder)

                print(f"  正在检查文件夹: {doi_folder} in {file_type_folder}")
                if doi_folder in valid_dois.values:
                    # 遍历子文件夹中的文件
                    for file_name in os.listdir(doi_folder_path):
                        file_path = os.path.join(doi_folder_path, file_name)

                        # 确保是文件，而不是子文件夹
                        if os.path.isfile(file_path):
                            # 使用祖父文件夹名来确定检查函数
                            check_function = check_functions.get(file_type_folder)

                            if check_function:
                                # 使用相应的检查函数检查文件
                                if utils.is_filename_valid(file_name, file_type_folder):

                                    with open(file_path, 'rb') as f:
                                        if check_function(f):
                                            print(f"    文件 {file_name} 通过了 {file_type_folder} 的检查")
                                            checked_files.append({
                                                'file_path': file_path,
                                                'file_type_folder': file_type_folder,
                                                'doi_folder': doi_folder
                                            })
                                            _flag, _formula, _adsorbate = utils.get_formula_adsorbate(file_type_folder,
                                                                                                      file_name)
                                            if _flag and _adsorbate is None:
                                                get_formulas.append(_formula)
                                                if _adsorbate not in adsorbate_dic.get(sheet_name, []):
                                                    adsorbates.append(_adsorbate)
                                        else:
                                            print(f"    错误: 文件 {file_name} 不符合 {file_type_folder} 文件类型要求")
                                            file_type_errs.append(f"Error: File  {file_name}  doesn't match {file_type_folder}. ")
                                else:
                                    filename_errs.append(f"{file_name} in {doi_folder} in {file_type_folder} doesn't match the rule.")
                        else:
                            print(f"    跳过非文件: {file_name}")
                    expected_formulas = valid_df[valid_df["DOI"] == doi_folder]['Formula'].tolist()
                    if get_formulas != expected_formulas and _flag:
                        get_formulas = "nothing" if len(get_formulas) == 0 else get_formulas
                        formula_errs.append(f"Expected {expected_formulas}, got {get_formulas} in {file_type_folder}/{doi_folder}")
                    if len(adsorbates) > 0:
                        filename_errs.append(f"Adsorbates: {adsorbates} out of range. ")
                    get_formulas = []
                    adsorbates = []
                else:
                    print(f"    跳过: {doi_folder}")
                    doi_errs.append(f"Skip: {doi_folder} in {file_type_folder}, Out of valid doi range. ")
        else:
            print(f"跳过非目标文件夹或非文件夹: {file_type_folder}")
        infos["doi"] = doi_errs if len(doi_errs) > 0 else None
        infos["substrate formula"] = formula_errs if len(formula_errs) > 0 else None
        infos["filename"] = filename_errs if len(filename_errs) > 0 else None
        infos["file_type"] = file_type_errs if len(file_type_errs) > 0 else None
    return checked_files, infos


def get_folder_content(file_type_folder, folder_path):
    folder_dict = []

    # 遍历 file_type_folder 下的每个子文件夹
    for doi_folder in os.listdir(folder_path):
        doi_folder_path = os.path.join(folder_path, doi_folder)

        # 确保子文件夹中有文件
        if os.path.isdir(doi_folder_path):
            files_in_folder = os.listdir(doi_folder_path)

            # 这里假设每个子文件夹下只有一个文件，根据文件名提取 formula
            if len(files_in_folder) > 0:
                for file_name in files_in_folder:
                    if utils.is_filename_valid(file_name, file_type_folder):
                        flag, formula, adsorbate = utils.get_formula_adsorbate(file_type_folder, file_name)
                        folder_dict.append((doi_folder, formula))
                    else:
                        folder_dict.append((doi_folder, None))

    return folder_dict


def check_folders_and_generate_df(extracted_path):
    # 定义要检查的文件类型文件夹
    valid_folders = ['CONTCAR', 'CIF', 'INCAR', 'KPOINTS', 'XYZ']

    # 初始化一个字典，用来存储每个 file_type_folder 对应的 DOI 和 Formula 列表
    folder_content_dict = defaultdict(list)

    # 遍历每个 file_type_folder
    for file_type_folder in valid_folders:
        folder_path = os.path.join(extracted_path, file_type_folder)

        # 确保文件夹存在
        if os.path.exists(folder_path):
            # 提取该文件夹下的 DOI 和 Formula
            folder_content = get_folder_content(file_type_folder, folder_path)
            folder_content_dict[file_type_folder].extend(folder_content)
        # else:
        #     print(f"{file_type_folder} 文件夹不存在")
        #     err.append(f"{file_type_folder} 文件夹不存在")
        #     continue

    # if len(err) > 0:
    #     return err, None

    # 初始化空列表，用于生成 DataFrame
    data = {
        "FileType": [],
        "DOI": [],
        "Formula": []
    }

    # 遍历文件内容字典，提取每个 file_type_folder 中的 DOI 和 Formula
    for file_type_folder, content in folder_content_dict.items():
        for doi_folder, formula in content:
            data["FileType"].append(file_type_folder)
            data["DOI"].append(doi_folder)
            data["Formula"].append(formula)

    # 生成 DataFrame
    df = pd.DataFrame(data)

    return df


def upload_files_to_google_drive(checked_files, folder_id_dict):
    """
    将通过检查的文件上传到 Google Drive 对应的路径。
    :param checked_files: 通过检查的文件信息列表 [{file_path, folder_name, subfolder_name}]
    :param folder_id_dict: 一个字典，key 是 folder_name，value 是 Google Drive 对应文件夹的 folder_id
    """
    print(checked_files)
    service = quickstart_googledrive.init_drive_client()  # 认证并获取 Google Drive 服务实例

    for file_info in checked_files:
        file_path = file_info['file_path']
        folder_name = file_info['folder_name']
        subfolder_name = file_info['subfolder_name']
        file_name = os.path.basename(file_path)

        print(f"正在上传文件: {file_name}")
        # 获取父文件夹 ID（例如 'computational_data' 下的 'folder_name' 文件夹）
        parent_folder_id = folder_id_dict.get(folder_name)

        if parent_folder_id:
            # 在 Google Drive 中创建 DOI 子文件夹
            doi_folder_id = quickstart_googledrive.create_or_get_subfolder(service, subfolder_name, parent_folder_id)

            # 将文件上传到 Google Drive 中的对应路径
            quickstart_googledrive.upload_or_replace_file(filename, file_path, "text/plain", doi_folder_id, service)
        else:
            print(f"未找到文件夹 {folder_name} 对应的 Google Drive folder_id")
            return "Something wrong uploading file to GDrive"


def extract_and_check_zip(uploaded_file, select_data_type, username):
    """解压上传的zip文件并检查是否包含相应的Excel文件"""
    output_dir = f"extracted_files_{username}"

    # 清理之前的解压文件
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    # 解压上传的zip文件
    try:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            for member in zip_ref.namelist():
                # 跳过 __MACOSX 文件夹和其他隐藏文件
                if not member.startswith('__MACOSX') and not member.startswith('.'):
                    zip_ref.extract(member, output_dir)
    except zipfile.BadZipFile:
        return f"Error: The file is not a valid zip file.", None

    # 根据选择的类型检查是否包含对应的Excel文件
    expected_excel = "computational_data.xlsx" if select_data_type == "Computational Structures(including adsorption free energies)" else None

    # 检查解压后的文件夹是否是合规的
    extracted_files = [os.path.join(output_dir, p) for p in os.listdir(output_dir) if check_folder_content(os.path.join(output_dir, p))]
    print("Extracted Files", extracted_files)
    if len(extracted_files) == 1:
        # 如果只有一个文件夹，进入该文件夹
        target_folder = extracted_files[0]
        target_files = os.listdir(target_folder)
        print(target_files)
    else:
        return "More than one file was extracted for this upload.", None

    if expected_excel not in target_files:
        return f"Error: {expected_excel} is not found in the zip file.", None

    # 返回解压目录路径以便后续使用
    return None, target_folder


def read_process_excel(extracted_dir, select_data_type, current_name, sheet_name, df=None):
    """
    读取上传的Excel文件并进行处理（去除空值，添加Uploader列）
    """
    # 根据选择的类型确定Excel文件路径
    excel_file = os.path.join(extracted_dir, "computational_data.xlsx") if select_data_type == "Computational Structures(including adsorption free energies)" else None

    # 读取Excel文件
    if excel_file is not None:
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
        except FileNotFoundError:
            return f"Error: Excel file {excel_file} not found.", None
        except Exception as e:
            return f"Error reading Excel file: {str(e)}", None
    else:
        df = pd.DataFrame({
            {"Formula": []},
            {"DOI": []},
        })
    # 去重
    df.dropna(axis=0, how='all', inplace=True)
    # 拼接姓名
    df["Uploader"] = current_name
    # 检查是否包含DOI列
    if "DOI" not in df.columns:
        return f"Error: DOI column not found in {excel_file}", None

    return None, df


def process_df_and_validate(df, current_name, select_type, sheet_name):
    """遍历DOI列表，检查合法性和匹配性，返回处理结果"""
    # 初始化空的DataFrame来存储结果
    invalid_doi_df = pd.DataFrame(columns=df.columns)   # 不合法DOI的整行数据
    unmatched_doi_df = pd.DataFrame(columns=df.columns)  # 不匹配DOI的整行数据
    valid_entries_df = pd.DataFrame(columns=df.columns)  # 有效DOI的整行数据

    for _, row in df.iterrows():  # 遍历DataFrame的每一行
        doi_in = row["DOI"]

        # 检查 DOI 是否合法
        if not utils.is_valid_doi(doi_in):
            invalid_doi_df = pd.concat([invalid_doi_df, row.to_frame().T], ignore_index=True)  # 存储不合法DOI的整行数据
            continue

        # 检查 DOI 是否与上传者匹配
        err = uploadStruc.is_doi_name_match(doi_in, current_name, select_type, sheet_name)
        if err is None:
            valid_entries_df = pd.concat([valid_entries_df, row.to_frame().T], ignore_index=True)  # 存储有效DOI的整行数据
        else:
            unmatched_doi_df = pd.concat([unmatched_doi_df, row.to_frame().T], ignore_index=True)

    # 返回结果，包含不合法DOI、不匹配DOI及其错误信息、有效DOI的整行数据
    return invalid_doi_df, unmatched_doi_df, valid_entries_df


# 整合的逻辑，用于处理文件上传并展示DOI检查结果
def handle_uploaded_file(uploaded_zip, select_upload_type, current_name, sheet_name):
    """
    处理上传的zip文件，解压并检查DOI合法性和匹配性
    :param uploaded_zip:
    :param select_upload_type:
    :param current_name: 当前登录name
    :param sheet_name: 反应名
    :return: 错误信息, pd.DataFrame, pd.DataFrame, pd.DataFrame
    """

    # Step 1: 解压文件并检查Excel
    err, extracted_dir = extract_and_check_zip(uploaded_zip, select_upload_type, current_name)
    if err:
        return err, None, None, None, None, None

    # Step 2: 读取Excel并处理df
    if select_upload_type == "Computational Structures(including adsorption free energies)":
        err, df = read_process_excel(extracted_dir, select_upload_type, current_name, sheet_name)
        if err:
            return err, None, None, None, None, None

        # Step 3: 遍历DOI列表并检查合法性和匹配性
        invalid_doi, unmatched, valid_entries = process_df_and_validate(df, current_name, select_upload_type,
                                                                        sheet_name)
    elif select_upload_type == "Computational Structures(without adsorption free energies)":
        err, df = check_folders_and_generate_df(extracted_dir)
        if err:
            return err, None, None, None, None
        invalid_doi, unmatched = None, None
        valid_entries = process_df_and_validate
    else:
        raise "select_upload_type out of range"

    checked_files, infos = check_subfolders_and_files(extracted_dir, valid_entries, sheet_name)

    # 返回结果
    return None, invalid_doi, unmatched, valid_entries, checked_files, infos


def update_or_insert_data(original_data: pd.DataFrame, new_data: pd.DataFrame):
    """
    遍历Excel文件中合法的DOI行，以 DOI 和 Formula 作为联合主键，进行更新或插入操作
    :param original_data: 原有的DataFrame数据
    :param new_data: 新的合法DOI行数据，DataFrame格式
    """
    for index, row in new_data.iterrows():
        doi = row["DOI"]
        formula = row["Formula"]

        # 查找是否已经存在对应的 DOI 和 Formula 的记录
        condition = (original_data["DOI"] == doi) & (original_data["Formula"] == formula)
        if condition.any():
            # 如果记录存在，进行更新
            original_data.loc[condition, :] = row.values
            print(f"Updated DOI: {doi}, Formula: {formula}")
        else:
            # 如果记录不存在，添加新行
            original_data = pd.concat([original_data, pd.DataFrame([row])], ignore_index=True)
            print(f"Inserted new DOI: {doi}, Formula: {formula}")

    return original_data


# 提交按钮绑定的主函数
def submit_data_to_file(valid_doi_data: pd.DataFrame, uploader_name, sheet_name):
    """
    接受包含合法DOI行的DataFrame，处理并上传到pkl文件。
    :param select_data_type: Exp OR Comp
    :param valid_doi_data: 已经经过合法性检查的DOI行数据 (DataFrame)
    :param uploader_name: 当前上传者的名字
    :param sheet_name: 反应名
    """

    # 根据选择的类型确定pkl文件路径
    pkl_file_path = './computational_data/computational_data.pkl'

    # Step 1: 加载现有的pkl文件
    try:
        total_dic = load_pkl_data(pkl_file_path)
        current_react_df = total_dic[sheet_name]
    except FileNotFoundError:
        return f"Error: File {pkl_file_path} not found."
    except Exception as e:
        return f"Error loading pkl file: {str(e)}"

    # Step 2: 为每一行数据添加上传者信息
    current_react_df["Uploader"] = uploader_name

    # Step 3: 更新或插入数据
    try:
        computational_data = update_or_insert_data(current_react_df, valid_doi_data)
    except Exception as e:
        return f"Error updating or inserting data: {str(e)}"

    # Step 4: 保存更新后的数据回pkl文件
    try:
        total_dic[sheet_name] = computational_data
        save_pkl_data(pkl_file_path, total_dic)
    except Exception as e:
        return f"Error saving pkl file: {str(e)}"

    # 返回None表示成功
    return None


if __name__ == '__main__':
    pd.read_excel(None)