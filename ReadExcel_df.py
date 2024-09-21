import pandas as pd
import numpy as np
import re
from datetime import datetime

from columns import type_list, subtype_dict, reaction_options


# 收集错误和设计高亮
def collect_errors_and_styles(_df, expected_columns, reaction, doi_db):
    # 用来储存错误位置和信息
    errors = {}
    _df = _df.dropna(how='all', axis=0,).reset_index(drop=True)
    styles = pd.DataFrame('', index=_df.index, columns=_df.columns)

    # 部分单位的转换
    equivalent_units = {
        'Celsius': ['°C', 'Celsius'],
        '°C': ['Celsius'],
        'bar': ['MPa'],
    }

    # 检查列名和反应方程式的对应
    # actual_columns = df.columns.tolist()
    # column_errors = [col for col in actual_columns if col not in expected_columns]
    # if len(column_errors) > 0:
    #     col_err_txt = []
    #     for col in column_errors:
    #         col_err_txt.append(f"Column name '{col}' does not match.")
    #     errors["Column"] = col_err_txt

    # 将包含 /, NA, N A 等字眼的值置为空值
    special_na_pattern = re.compile(r'^\s*(/|NA|N\s*A)\s*$', re.IGNORECASE)
    for col in _df.columns:
        for i, value in enumerate(_df[col]):
            if pd.notna(value) and special_na_pattern.match(str(value).strip()):
                _df.at[i, col] = np.nan  # 将匹配的特殊值置为空值

    # 用来储存可以通过的DOI，以便在判断连号时使用
    doi_errors = []
    valid_dois_with_indices = []
    valid_dois_list = []
    doi_rm_ls = []
    doi_pattern = re.compile(r'10\.\d+\/[\w.\-\/]+')
    index_to_drop = []
    # 检查DOI列
    if "DOI" in _df.columns:
        for i, value in enumerate(_df["DOI"]):
            if pd.notna(value):
                value = str(value).strip()
                if not value.lower() == "unpublished":
                    matches = doi_pattern.findall(value)
                    if matches:
                        matched_doi = matches[0]
                        if matched_doi not in doi_db:
                            # 检查是否完全正确的DOI
                            if value != matched_doi:
                                _df.at[i, "DOI"] = matched_doi
                                styles.at[i, "DOI"] = 'background-color: orange; color: black;'
                                doi_errors.append(f"DOI has been modified in row {i}, 'DOI' column.")
                            # 储存匹配的DOI
                            valid_dois_with_indices.append((i, matched_doi))
                            valid_dois_list.append(matched_doi)
                        else:
                            index_to_drop.append(i)
                    else:
                        styles.at[i, "DOI"] = 'background-color: orange; color: black;'
                        doi_errors.append(f"Row {i} in the 'DOI' column does not contain a valid DOI")

        # 去掉重复的DOI
        seen_dois = set()
        unique_dois_with_indices = []
        for index, doi in valid_dois_with_indices:
            if doi not in seen_dois:
                unique_dois_with_indices.append((index, doi))
                seen_dois.add(doi)

        # 找到最后一个“数字”
        def find_last_digit_index(s):
            for idx in range(len(s) - 1, -1, -1):
                if s[idx].isdigit():
                    return idx
            return -1

        # 记录标记过的索引
        processed_indices = set()

        # 判断DOI的连号
        for i in range(1, len(unique_dois_with_indices)):
            prev_index, prev_doi = unique_dois_with_indices[i - 1]
            curr_index, curr_doi = unique_dois_with_indices[i]

            # 检查二者长度
            if len(prev_doi) == len(curr_doi):
                # 找到最后一个数字
                prev_last_digit_index = find_last_digit_index(prev_doi)
                curr_last_digit_index = find_last_digit_index(curr_doi)

                # 检查最后的数字的索引位置
                if prev_last_digit_index == curr_last_digit_index:
                    # 移除最后的数字
                    prev_doi_without_last = prev_doi[:prev_last_digit_index] + prev_doi[prev_last_digit_index + 1:]
                    curr_doi_without_last = curr_doi[:curr_last_digit_index] + curr_doi[curr_last_digit_index + 1:]

                    # 检查移除后是否完全相同
                    if prev_doi_without_last == curr_doi_without_last:
                        # 如果没有标记，则标记该位置
                        for index in [prev_index, curr_index]:
                            if index not in processed_indices:
                                styles.at[index, "DOI"] = 'background-color: red; color: white;'  # Red for DOI range errors
                                doi_errors.append(f"Sequential DOI found in row {index}, 'DOI' column")
                                doi_rm_ls.append(_df.at[index, "DOI"])  # 确保存储的是原始 DOI
                                processed_indices.add(index)
        for e in doi_rm_ls:
            valid_dois_list.remove(e)
        if len(doi_errors) > 0:
            errors["DOI"] = doi_errors

    # 检查中文字符
    chinese_errors = []
    for col in _df.columns:
        for i, value in enumerate(_df[col]):
            if pd.notna(value) and re.search(r'[\u4e00-\u9fff]', str(value)):
                styles.at[i, col] = 'background-color: orange; color: black;'
                chinese_errors.append(f"Contains Chinese characters in row {i}, '{col}' column.")
    if len(chinese_errors) > 0:
        errors["Chinese"] = chinese_errors

    # 检查Type列
    type_errors = []
    if "Type" in _df.columns:
        for i, value in _df['Type'].items():
            if pd.notna(value) and value not in type_list:
                styles.at[i, 'Type'] = 'background-color: red; color: white;'
                type_errors.append(f"Type '{value}' not found in row {i}, 'Type' column.")
    if len(type_errors) > 0:
        errors["Type"] = type_errors

    # 检查SubType列，必须Type列正确才执行检查
    subtype_errors = []
    if "Type" in _df.columns and "subType" in _df.columns:
        for i, (type_val, subtype_val) in _df[['Type', 'subType']].iterrows():
            if pd.notna(type_val) and pd.notna(subtype_val) and type_val in type_list:
                if subtype_val not in subtype_dict.get(type_val, []):
                    styles.at[i, 'subType'] = 'background-color: blue; color: white;'
                    subtype_errors.append(f"SubType '{subtype_val}' mismatch in row {i}, 'subType' column.")
    if len(subtype_errors) > 0:
        errors["SubType"] = subtype_errors

    # 检查Content列
    if "Content" in _df.columns:
        content_errors = []
        chemical_pattern = re.compile(r'^([A-Z][a-z]?\d*)+$')
        number_pattern = re.compile(r'^\d+(\.\d+)?%?$')
        unit_pattern = re.compile(r'^(wt\.?|at\.?)%(;\s*(wt\.?|at\.?)%)?$')

        for i, value in enumerate(_df["Content"]):
            if pd.notna(value):
                value = str(value).strip()

                # Find the index of the first '=' or ':'
                separator_match = re.search(r'[=:]', value)
                if separator_match:
                    sep_index = separator_match.start()
                    first_part = value[:sep_index].strip()
                    remaining_part = value[sep_index + 1:].strip()

                    # 寻找单位索引
                    letter_index = re.search(r'[a-zA-Z]', remaining_part)
                    if letter_index:
                        letter_index = letter_index.start()
                        third_part = remaining_part[:letter_index].strip()
                        fourth_part = remaining_part[letter_index:].strip()

                        # 第一部分
                        chemicals = first_part.split('/')
                        for chem in chemicals:
                            if not chemical_pattern.fullmatch(chem):
                                styles.at[
                                    i, "Content"] = 'background-color: green; color: white;'
                                content_errors.append(f"In row {i}, chemical formula error in the 'Content' column")
                                break
                            elif not re.match(r'^([A-Z][a-z]?\d*)+$', chem):
                                styles.at[
                                    i, "Content"] = 'background-color: green; color: white;'
                                content_errors.append(f"In row {i}, invalid separator in the chemical formula in the 'Content' column")
                                break

                        # 第三部分(numbers)
                        numbers = third_part.split('/')
                        for num in numbers:
                            if not number_pattern.fullmatch(num):
                                styles.at[
                                    i, "Content"] = 'background-color: green; color: white;'
                                content_errors.append(f"In row {i}, number format error in the 'Content' column")
                                break
                            elif not re.match(r'^\d+(\.\d+)?%?$', num):
                                styles.at[
                                    i, "Content"] = 'background-color: green; color: white;'
                                content_errors.append(f"In row {i}, invalid separator in numbers in the 'Content' column")
                                break

                        if not len(chemicals) == len(numbers):
                            styles.at[i, "Content"] = 'background-color: green; color: white;'
                            content_errors.append(f"In row {i}, count mismatch error in the 'Content' column")

                        # Validate the fourth part (units)
                        if not unit_pattern.fullmatch(fourth_part):
                            styles.at[i, "Content"] = 'background-color: green; color: white;'
                            content_errors.append(f"In row {i}, unit format error in the 'Content' column")

                    else:
                        styles.at[i, "Content"] = 'background-color: green; color: white;'
                        content_errors.append(f"In row {i}, missing letter in the remaining part of the 'Content' column")

                else:
                    styles.at[i, "Content"] = 'background-color: green; color: white;'
                    content_errors.append(f"In row {i}, missing separator in the 'Content' column")

        if len(content_errors) > 0:
            errors["Content"] = content_errors

        # 检查条件列（包含@）
        condition_errors = []
        condition_pattern = re.compile(r'^[-+]?\d+(\.\d+)?@\s*[-+]?\d+(\.\d+)?(\s*[a-zA-Z/%-]*)?$')
        conditional_columns = [col for col in _df.columns if '@' in col]
        for col in conditional_columns:
            for i, value in enumerate(_df[col]):
                if pd.notna(value):
                    value = str(value).strip()  # 去掉前后空格
                    match = condition_pattern.match(value)
                    if not match:
                        # 标记错误的单元格位置
                        condition_errors.append(f"In row {i}, the value '{value}' in the '{col}' column does not match the required format")
                        styles.at[i, col] = 'background-color: blue; color: white;'

        if len(condition_errors) > 0:
            errors["Condition"] = condition_errors

    # 找到带有单位的列
    unit_errors = []
    unit_columns = [col for col in _df.columns if re.search(r'\(.*\)', col)
                    and '@' not in col
                    and col != "Other product (FE > 10%)"]
    for col in unit_columns:
        # 从列名中提取单位
        unit_col_match = re.search(r'\((.*?)\)', col)
        if unit_col_match:
            unit_col = unit_col_match.group(1).strip()  # 提取并清理单位

            # 编译用于检查纯数字的正则表达式
            number_pattern = re.compile(r'^[<>≤≥]?\d+(\.\d+)?(±\d+(\.\d+)?)?$')

            for i, value in enumerate(_df[col]):
                if pd.notna(value):
                    value = str(value).strip()  # 去除两端空格

                    # 1. 检查是否为纯数字
                    if number_pattern.match(value):
                        # 是纯数字，直接通过
                        continue

                    # 2. 检查数字和单位的情况
                    number_match = re.match(r'^(\d+(\.\d+)?)(.*)$', value)
                    if number_match:
                        number_part = number_match.group(1)
                        unit_value = number_match.group(3).strip()  # 获取数字后的内容

                        # 检查是否包含括号
                        unit_value_match = re.search(r'\((.*?)\)', unit_value)
                        if unit_value_match:
                            unit_value = unit_value_match.group(1).strip()  # 提取括号内的内容
                        else:
                            unit_value = unit_value.strip()  # 如果没有括号，直接使用原值

                        # 3. 比较 unit_value 和 unit_col，考虑等价替换
                        if unit_value != unit_col and unit_value not in equivalent_units.get(unit_col, []):
                            # 不匹配，标记错误
                            styles.at[
                                i, col] = 'background-color: purple; color: white;'  # Purple for unit format errors
                            unit_errors.append(f"In row {i}, the unit in the '{col}' column is invalid or mismatched")
                    else:
                        # 格式不匹配
                        styles.at[i, col] = 'background-color: purple; color: white;'  # Purple for unit format errors
                        unit_errors.append(f"In row {i}, the value format in the '{col}' column is invalid")

    if len(unit_errors) > 0:
        errors["Unit"] = unit_errors

    # 检查反应产物
    product_errors = []
    if reaction in reaction_options.keys():
        for key in reaction_options[reaction].keys():
            key = key.strip()
            if key in _df.columns:
                for i, value in enumerate(_df[key]):
                    if pd.notna(value):
                        value = str(value).strip()
                        if value not in reaction_options[reaction][key]:
                            product_errors.append(
                                f"In row {i}, the value '{value}' in the '{key}' column for reaction '{reaction}' is invalid")
                            styles.at[i, key] = 'background-color: yellow; color: black;'
    if len(product_errors) > 0:
        errors["Product"] = product_errors

    # Year列 的正则表达式模式：四位整数
    if "Year" in _df.columns:
        year_errors = []
        year_pattern = re.compile(r'^\d{4}$')
        # 获取当前年份
        current_year = datetime.now().year
        # 检查 Year 列的值
        for i, value in enumerate(_df['Year']):
            if pd.notna(value):
                value = str(value).strip()  # 去掉前后空格
                if year_pattern.match(value):
                    year = int(value)
                    # 检查年份是否在1900到当前年份之间
                    if not (1900 <= year <= current_year):
                        year_errors.append(
                            f"In row {i}, the value '{value}' in the 'Year' column is out of the valid range (1900-{current_year})")
                        styles.at[i, 'Year'] = 'background-color: red; color: white;'
                else:
                    # 如果不匹配四位整数，直接标记为格式错误
                    year_errors.append(f"In row {i}, the value '{value}' in the 'Year' column does not match the required format")
                    styles.at[i, 'Year'] = 'background-color: red; color: white;'
        if len(year_errors) > 0:
            errors["Year"] = year_errors

    styles = styles.drop(index_to_drop)
    _df = _df.drop(index_to_drop)

    return errors, styles, list(set(valid_dois_list)), _df

