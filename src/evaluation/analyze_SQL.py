import json
from utils import extract_sql, analyze_sql_patterns, analyze_sqls_complexity

def main():
    # 1. 从数据文件中提取 SQL 查询
    sql_file_path = "data/dev.sql"
    n_gram_size= 5
    # queries_list = extract_sql(sql_file_path)
    queries_list = extract_sql(sql_file_path)

    # 2. 分析 SQL 模式（可选的 n-gram 特征分析）
    # patterns_result = analyze_sql_patterns(queries_list, n_gram_size)
    # print(patterns_result)

    # 3. 分析 SQL 的复杂度（token 数、JOIN 数、关键词数）并写入 CSV
    output_csv_path = "results/preprocess/output_analysis.csv"
    analyze_sqls_complexity(queries_list, output_csv_path)

    print("✅ 所有分析完成。")

if __name__ == "__main__":
    main()
