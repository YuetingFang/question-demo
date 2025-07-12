import json
import os
import pandas as pd
from pathlib import Path


'''
将存储在 csv 文件的 column and value descriptions 提取，再存入到 json 文件中 
'''

def extract_schema_fields_multiple(json_path, target_db_ids=None):
    """
    读取 JSON 文件，返回符合 target_db_ids 的所有 schema 数据列表。
    如果 target_db_ids 为 None，返回所有 db 条目。
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    if target_db_ids is None:
        # 返回全部条目
        result = []
        for db in data:
            filtered_db = {k: db[k] for k in [
                "db_id", "table_names_original", "table_names",
                "column_names_original", "column_names",
                "column_types", "primary_keys", "foreign_keys"
            ]}
            result.append(filtered_db)
        return result

    # 返回指定的 db_id 条目
    result = []
    for db in data:
        if db.get("db_id") in target_db_ids:
            filtered_db = {k: db[k] for k in [
                "db_id", "table_names_original", "table_names",
                "column_names_original", "column_names",
                "column_types", "primary_keys", "foreign_keys"
            ]}
            result.append(filtered_db)
    return result


def clean_val(val):
    if val is None:
        return None
    if isinstance(val, float):
        # NaN 是 float 类型
        import math
        if math.isnan(val):
            return None
    if isinstance(val, str):
        # 空字符串或者字符串 'nan' 都可以替换
        if val.strip().lower() == 'nan' or val.strip() == '':
            return None
    return val


def extract_table_descriptions(schema_data, csv_folder_path):
    column_desc_output = []
    value_desc_output = []

    column_names_original = schema_data["column_names_original"]
    table_names_original = schema_data["table_names_original"]

    for table_index, col_name in column_names_original:
        if table_index == -1:
            column_desc_output.append([-1, "*"])
            value_desc_output.append([-1, "*"])
            continue

        table_name = table_names_original[table_index]
        csv_path = os.path.join(csv_folder_path, f"{table_name}.csv")

        if not os.path.exists(csv_path):
            print(f"⚠️ 未找到 CSV 文件：{csv_path}")
            column_desc_output.append([table_index, None])
            value_desc_output.append([table_index, None])
            continue

        try:
            # 首先尝试使用 utf-8 编码读取
            df = pd.read_csv(csv_path, dtype=str, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                # 如果 utf-8 失败，尝试 gbk 编码（常见于中文Windows）
                df = pd.read_csv(csv_path, dtype=str, encoding='gbk')
            except UnicodeDecodeError:
                try:
                    # 如果 gbk 也失败，尝试 latin1 编码（不会抛出解码错误）
                    df = pd.read_csv(csv_path, dtype=str, encoding='latin1')
                except Exception as e:
                    print(f"❌ 无法读取文件 {csv_path}，错误: {str(e)}")
                    column_desc_output.append([table_index, None])
                    value_desc_output.append([table_index, None])
                    continue

        if "original_column_name" not in df.columns or \
           "column_description" not in df.columns or \
           "value_description" not in df.columns:
            print(f"⚠️ 文件缺字段：{csv_path}")
            column_desc_output.append([table_index, None])
            value_desc_output.append([table_index, None])
            continue

        row = df[df["original_column_name"] == col_name]
        if not row.empty:
            column_description = clean_val(row.iloc[0]["column_description"])
            value_description = clean_val(row.iloc[0]["value_description"])
        else:
            column_description = None
            value_description = None

        column_desc_output.append([table_index, column_description])
        value_desc_output.append([table_index, value_description])

    return column_desc_output, value_desc_output


def build_final_json(schema_data, column_desc_list, value_desc_list, output_path):
    final_data = {
        "db_id": schema_data["db_id"],
        "table_names_original": schema_data["table_names_original"],
        "table_names": schema_data["table_names"],
        "column_names_original": schema_data["column_names_original"],
        "column_names": schema_data["column_names"],
        "column_descriptions_original": column_desc_list,
        "value_descriptions_original": value_desc_list,
        "column_types": schema_data["column_types"],
        "primary_keys": schema_data["primary_keys"],
        "foreign_keys": schema_data["foreign_keys"]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)

    print(f"✅ 输出文件已保存到：{output_path}")




# all datasets
def main():
    json_path = "data/dev_tables.json"
    # json_path = "train/train_tables.json"

    all_schema_data = extract_schema_fields_multiple(json_path)

    final_output_list = []

    for schema_data in all_schema_data:
        db_id = schema_data["db_id"]
        csv_folder = Path("data/dev_databases") / db_id / "database_description"
        # csv_folder = Path("train/train_databases") / db_id / "database_description"

        column_desc_list, value_desc_list = extract_table_descriptions(schema_data, csv_folder)

        final_data = {
            "db_id": schema_data["db_id"],
            "db_overview": [],
            "table_names_original": schema_data["table_names_original"],
            "table_names": schema_data["table_names"],
            "column_names_original": schema_data["column_names_original"],
            "column_names": schema_data["column_names"],
            "column_descriptions_original": column_desc_list,
            "column_descriptions": [],
            "value_descriptions_original": value_desc_list,
            "column_types": schema_data["column_types"],
            "primary_keys": schema_data["primary_keys"],
            "foreign_keys": schema_data["foreign_keys"]
        }

        final_output_list.append(final_data)

    # 最终统一写入一个 JSON 文件
    output_json_path = "results/preprocess/preprocess_dev_tables.json"
    # output_json_path = "train/refine_train_tables.json"
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(final_output_list, f, indent=4, ensure_ascii=False)

    print(f"✅ 所有 db 已写入统一文件：{output_json_path}")

if __name__ == "__main__":
    main()
