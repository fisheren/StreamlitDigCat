import os
import shutil
import zipfile

import pandas as pd

import authentic_file
from upload2DB import DatabaseUploader
from utils import is_filename_valid, get_formula_adsorbate, is_valid_doi, check_functions, is_doi_name_match


class FileValidator:
    struc_file_types = ["CONTCAR", "CIF", "XYZ"]

    def __init__(self, uploaded_file, uploader, sheet_name):
        """
        类初始化时自动解压并检查上传的zip文件。
        若出现错误则将错误信息加入self.error_messages并终止后续操作。
        """
        self.valid_expected_df: pd.DataFrame = pd.DataFrame()

        self.valid_types: dict = check_functions

        self.valid_data = []
        self.error_messages = []
        self.base_dir = None  # 用于存储成功解压后的目录路径
        self.checked_files = []

        self.reaction_name = sheet_name
        self.has_free_energy = False
        self.uploader = uploader

        self.db_conn = DatabaseUploader(authentic_file.config.DB_URL)

        # 调用解压和检查zip文件的函数
        target_folder = self.extract_and_check_zip(uploaded_file)
        if target_folder is None:
            return  # 遇到错误，终止初始化过程
        else:
            self.base_dir = target_folder  # 成功解压并验证后的目标目录路径
        self.generate_valid_df()

    def __del__(self):
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
            print(f"Deleted folder {self.base_dir}")

    def extract_and_check_zip(self, uploaded_file):
        """解压上传的zip文件并检查是否包含相应的Excel文件"""
        output_dir = f"extracted_files_{self.uploader}"

        # 清理之前的解压文件
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        # 解压上传的zip文件
        try:
            with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    # 跳过 需要忽略的文件
                    if not self.is_ignored_file(member):
                        zip_ref.extract(member, output_dir)
        except zipfile.BadZipFile:
            self.error_messages.append("Error: The file is not a valid zip file.")
            return None

        # 根据选择的类型检查是否包含对应的Excel文件
        expected_excel = "computational_data.xlsx"

        # 检查解压后的文件夹是否合规
        extracted_files = os.path.join(output_dir, os.listdir(output_dir)[0])
        if len(os.listdir(output_dir)) == 1:
            # 如果只有一个文件夹，进入该文件夹
            target_folder = extracted_files
            target_files = os.listdir(target_folder)
            print(target_files)
        else:
            self.error_messages.append("Error: More than one file was extracted for this upload.")
            return None

        if expected_excel in target_files:
            self.has_free_energy = True

        # 返回解压目录路径
        return target_folder

    @staticmethod
    def is_ignored_file(file_name):
        """检查文件是否是需要忽略的文件"""
        return (
                file_name.startswith('.') or
                file_name.startswith('_') or
                file_name.startswith('~') or
                file_name in ['ignore.txt', 'temp_file.tmp'])  # 可以根据需要增加不相关文件

    def validate_files(self):
        """遍历文件夹并检查每个文件的合法性"""
        for file_type_folder in os.listdir(self.base_dir):
            file_type_path = os.path.join(self.base_dir, file_type_folder)

            # 确保是一个文件夹并且是有效的类型
            if os.path.isdir(file_type_path) and file_type_folder in self.valid_types:
                for doi_folder in os.listdir(file_type_path):
                    doi_path = os.path.join(file_type_path, doi_folder)
                    doi_folder = doi_folder.replace(':', '/').replace('-', '/')
                    # 确保是一个有效的 DOI 文件夹
                    if os.path.isdir(doi_path) and is_valid_doi(doi_folder):
                        for file_name in os.listdir(doi_path):
                            if self.is_ignored_file(file_name):
                                continue  # 如果文件是需要忽略的，则跳过

                            file_path = os.path.join(doi_path, file_name)

                            if os.path.isfile(file_path):
                                self.check_file(file_type_folder, file_name, file_path, doi_folder)

    def check_file(self, file_type_folder, file_name, file_path, doi_folder):
        """检查单个文件的合法性"""
        print(f"Checking {file_name} in {file_type_folder}/{doi_folder}")
        with open(file_path, 'rb') as file:
            is_valid_type = self.valid_types[file_type_folder](file)
        is_valid_name = is_filename_valid(file_name, file_type_folder)

        if not is_valid_type:
            self.error_messages.append(
                f"File type mismatch: You uploaded {file_name} located in {file_type_folder}/{doi_folder.replace('/','-')}. But expected: {file_type_folder}")

        if not is_valid_name:
            self.error_messages.append(
                f"Invalid file naming: You uploaded {file_name} located in {file_type_folder}/{doi_folder.replace('/','-')}")

        if is_valid_type and is_valid_name:
            # 提取 DOI、formula 和 adsorbate 信息
            doi = doi_folder  # 假设 doi_folder 名称即为 DOI
            formula, adsorbate = get_formula_adsorbate(file_name)
            if adsorbate in self.db_conn.get_valid_ads_ls(self.reaction_name) or adsorbate is None:
                self.valid_data.append(
                    {'DOI': doi, 'Formula': formula, 'AdsorbateName': adsorbate, 'FileType': file_type_folder})
                self.checked_files.append({
                    'file_path': file_path,
                    'file_type_folder': file_type_folder,
                    'doi_folder': doi_folder
                })
            else:
                self.error_messages.append(
                    f"Adsorbate mismatch: You chose {self.reaction_name}, but there is no valid adsorbate {adsorbate}. {file_name} Located in {file_type_folder}/{doi_folder.replace('/','-')}"
                )

    def generate_valid_df(self):
        self.validate_files()
        return

    @staticmethod
    def transform_adsorbate_df(df):
        """
        转换 DataFrame，将 'Adsorbate1' 和 'Adsorbate2' 列展开成 'AdsorbateName' 和 'Energy' 列。

        :param df: pd.DataFrame: 原始的 DataFrame，包含 'Formula'、'DOI'、'Adsorbate1'、'Adsorbate2' 和 'Uploader' 列。

        :return: pd.DataFrame: 转换后的 DataFrame，包含 'Formula'、'DOI'、'Uploader'、'AdsorbateName' 和 'Energy' 列。
        """
        # 获取除 'Formula'、'DOI'、'Uploader' 之外的所有列
        value_vars = [col for col in df.columns if col not in ['DOI', 'Formula', 'Uploader', 'ReactionName']]
        # 使用 pd.melt 将 Adsorbate1 和 Adsorbate2 展开为行
        df_melted = df.melt(
            id_vars=['DOI', 'Formula'],
            value_vars=value_vars,
            var_name='AdsorbateName',
            value_name='FreeEnergy'
        )

        # 删除 Energy 列中为空的行
        df_cleaned = df_melted.dropna(subset=['FreeEnergy']).reset_index(drop=True)

        return df_cleaned

    def read_expected_df(self):
        """
        读取上传的Excel文件并进行处理（去除空值，添加Uploader列）
        # 根据选择的类型确定Excel文件路径
        :return:
        """
        excel_file = os.path.join(self.base_dir, "computational_data.xlsx") if self.has_free_energy else None

        # 如果文件路径有效，读取 Excel 文件
        if excel_file is not None:
            try:
                df = pd.read_excel(excel_file, sheet_name=self.reaction_name)
            except Exception as e:
                self.error_messages.append(f"Error reading Excel file: {str(e)}")
                return None
        else:
            df = pd.DataFrame(self.valid_data).drop(['FileType'], axis=1)

        # 检查是否包含 DOI 列
        if "DOI" not in df.columns:
            self.error_messages.append(f"Error: DOI column not found")
            return None
        else:
            # 去除全为空的行
            df.dropna(axis=0, how='all', inplace=True)

            # df["Uploader"] = self.uploader
            # df["ReactionName"] = self.reaction_name

            # 替换 DOI 列中的特殊字符
            df['DOI'] = df['DOI'].apply(lambda x: x.replace(':', '/').replace('-', '/') if isinstance(x, str) else x)

            if excel_file is not None:
                return self.transform_adsorbate_df(df)
            else:
                return df

    @staticmethod
    def get_required_df(df):
        """
        从 DataFrame 中提取唯一的 (DOI, Formula) 组合，并返回新的 DataFrame。

        :param: df (pd.DataFrame): 包含 'DOI' 和 'Formula' 列的原始 DataFrame。

        :return: pd.DataFrame: 包含唯一 (DOI, Formula) 组合的新 DataFrame。
        """
        # 提取唯一的 (DOI, Formula) 组合
        unique_combinations = df[['DOI', 'Formula']].drop_duplicates().reset_index(drop=True)

        return unique_combinations

    def validate_df_doi(self, df):
        """
        检查传入的DataFrame中的DOI列是否合法，并与上传者匹配。
        对于不合法或不匹配的DOI行，将错误信息加入self.error_messages。

        返回一个包含有效DOI的DataFrame。
        """
        valid_entries_df = pd.DataFrame(columns=df.columns)  # 有效DOI的行数据

        for _, row in df.iterrows():  # 遍历 DataFrame 的每一行
            doi_in = row["DOI"]

            # 检查 DOI 的合法性
            if not is_valid_doi(doi_in):
                self.error_messages.append(f"Invalid DOI format: {doi_in}")
                continue

            # 检查 DOI 是否与上传者匹配
            err = is_doi_name_match(doi_in, self.uploader, self.has_free_energy, self.reaction_name)
            if err is None:
                # DOI 合法且匹配，加入到 valid_entries_df 中
                valid_entries_df = pd.concat([valid_entries_df, row.to_frame().T], ignore_index=True)
            else:
                # DOI 匹配失败，记录错误信息
                self.error_messages.append(err)

        # 返回有效 DOI 的 DataFrame
        return valid_entries_df

    def validate_required_files(self, expected_df, got_df):
        """
        验证 got_df 中是否包含 expected_df 中要求的每条记录的至少一个文件类型。
        :param expected_df: (pd.DataFrame): 包含 'DOI'、'Formula' 和 'AdsorbateName' 列的 DataFrame。
        :param got_df: (pd.DataFrame): 包含 'DOI'、'Formula'、'AdsorbateName' 和 'FileType' 列的 DataFrame。
        :return: pd.DataFrame: 包含 'DOI'、'Formula' 及缺少的文件类型信息。
        """
        # 创建一个空列表用于记录缺失的文件类型
        validation_issues = []

        # 检查缺失的文件类型
        for _, row in expected_df.iterrows():
            doi = row['DOI']
            formula = row['Formula']
            adsorbate = None

            # 筛选 got_df 中符合 DOI、Formula 和 Adsorbate 的记录
            got_files = got_df[
                (got_df['DOI'] == doi) &
                (got_df['Formula'] == formula) &
                (got_df['AdsorbateName'].isna()) &
                (got_df['FileType'].apply(lambda x: True if x in self.struc_file_types else False))
                ]['FileType'].tolist()

            # 如果 got_df 中没有满足条件的文件记录，说明缺少该类型
            if not got_files:
                validation_issues.append({
                    'DOI': doi,
                    'Formula': formula,
                    'AdsorbateName': adsorbate,
                    'Issue': 'Missing at least one required structure file'
                })

        # 检查多余的文件类型
        for _, row in got_df.iterrows():
            doi = row['DOI']
            formula = row['Formula']
            adsorbate = row['AdsorbateName']

            # 检查 (DOI, Formula) 是否在 expected_df 中存在
            is_extra = expected_df[
                (expected_df['DOI'] == doi) &
                (expected_df['Formula'] == formula)
                ].empty

            # 如果该记录在 expected_df 中不存在，则认为这是多余文件
            if is_extra:
                validation_issues.append({
                    'DOI': doi,
                    'Formula': formula,
                    'AdsorbateName': adsorbate,
                    'Issue': 'Extra file not required by expected data'
                })

        # 将缺失的记录转换为 DataFrame
        issues_df = pd.DataFrame(validation_issues)

        # 如果存在问题，将每条问题添加到 self.error_messages 中
        if not issues_df.empty:
            for _, issue in issues_df.iterrows():
                self.error_messages.append(
                    f"Mismatched ERROR: Expected Data ({issue['DOI']}, {issue['Formula']}, "
                    f"Adsorbate={issue['AdsorbateName']}) -- {issue['Issue']}"
                )

        return issues_df

    def check_all(self):
        expected_df = self.read_expected_df()
        if expected_df is None:
            return {"Errors": self.error_messages}

        got_df = pd.DataFrame(self.valid_data)

        valid_expected_df = self.validate_df_doi(expected_df)
        self.valid_expected_df = valid_expected_df
        required_df = self.get_required_df(valid_expected_df)

        self.validate_required_files(required_df, got_df)
        return valid_expected_df, self.error_messages.copy()

    def submit_data2DB(self):
        df2upload = self.valid_expected_df
        df2upload["AdsorbateName"] = df2upload["AdsorbateName"].apply(lambda x: "Substrate" if x is None else x)
        df2upload["Uploader"] = self.uploader
        df2upload["ReactionName"] = self.reaction_name
        try:
            self.db_conn.upload_energy_data(df2upload)
            return None
        except Exception as e:
            return f"Error Submitting data to DB: {str(e)}"

    def submit_file_data2DB(self):
        df2upload = pd.DataFrame(self.valid_data)
        df2upload["AdsorbateName"] = df2upload["AdsorbateName"].apply(lambda x: "Substrate" if x is None else x)
        df2upload["Uploader"] = self.uploader
        df2upload["ReactionName"] = self.reaction_name
        try:
            self.db_conn.upload_file_data(df2upload)
            return None
        except Exception as e:
            return f"Error Submitting data to DB: {str(e)}"

    def save_local_files(self):
        """将检查过的文件保存到本地目录"""
        base_path = "./computational_data"  # 定义基础路径

        for file_info in self.checked_files:
            # 构建保存文件的路径
            file_type_folder = file_info['file_type_folder']
            doi_folder = file_info['doi_folder'].replace('/', '-')
            destination_folder = os.path.join(base_path, file_type_folder, doi_folder)

            # 创建目标文件夹（如果不存在）
            os.makedirs(destination_folder, exist_ok=True)

            # 目标文件路径
            file_path = file_info['file_path']
            destination_path = os.path.join(destination_folder, os.path.basename(file_path))

            # 将文件复制到目标位置
            shutil.copy(file_path, destination_path)
            print(f"Saved {file_path} to {destination_path}")

        print("All files have been saved successfully.")
