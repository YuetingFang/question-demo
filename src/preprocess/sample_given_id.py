import numpy as np
import random
import json
import os

random.seed(7)

given_qid = np.array([
    [1486, 1474, 1481],
    [1477, 1479, 0],
    [1508, 1509, 0],
    [1470, 1475, 0],
    [1511, 1473, 0],
    [1505, 1516, 1476],
    [1471, 1490, 1482],
    [1524, 1520, 0],
    [1508, 1472, 1526]
])

# 记录所选元素的值
selected_values = []

# 1. 在第三列随机选择 1 个 > 0 的元素
col3_indices = [i for i in range(8) if given_qid[i, 2] > 0]
if not col3_indices:
    raise ValueError("第三列中没有大于 0 的元素")
row3 = random.choice(col3_indices)
selected_values.append(given_qid[row3, 2])

# 2. 在第二列随机选择 6 个 > 0 的元素，且不在 row3 行
col2_indices = [i for i in range(8) if i != row3 and given_qid[i, 1] > 0]
if len(col2_indices) < 6:
    raise ValueError("第二列中满足条件的元素不足 6 个")
rows2 = random.sample(col2_indices, 6)
selected_values.extend([given_qid[i, 1] for i in rows2])

# 3. 在第一列随机选择 1 个 > 0 的元素，且不在 row3 和 rows2 中
col1_indices = [i for i in range(8) if i != row3 and i not in rows2 and given_qid[i, 0] > 0]
if not col1_indices:
    raise ValueError("第一列中没有满足条件的主选元素")
row1_main = random.choice(col1_indices)
selected_values.append(given_qid[row1_main, 0])

# 4. 在第一列再选 2 个 > 0 的元素，不能和 row1_main 相同，值不能重复
col1_remaining = [
    i for i in range(8)
    if i != row1_main and given_qid[i, 0] > 0 and given_qid[i, 0] != given_qid[row1_main, 0]
]
# 去除已经选过的值
used_values = {given_qid[row1_main, 0]}
col1_unique = [(i, given_qid[i, 0]) for i in col1_remaining if given_qid[i, 0] not in used_values]
if len(col1_unique) < 2:
    raise ValueError("第一列中没有足够的不重复大于0的元素")
additional_rows = random.sample(col1_unique, 2)
selected_values.extend([val for _, val in additional_rows])

# 从dev.json提取选中question_id的样例
# 确保输出目录存在
output_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + '/results/preprocess'
os.makedirs(output_dir, exist_ok=True)

# 读取dev.json文件
dev_file_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + '/data/dev.json'

with open(dev_file_path, 'r', encoding='utf-8') as f:
    dev_data = json.load(f)

# 筛选出符合selected_id的样例
filtered_data = [item for item in dev_data if item['question_id'] in selected_values]

# 将筛选结果保存到新的JSON文件
output_file_path = output_dir + '/sampled_debit_card.json'
with open(output_file_path, 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f, ensure_ascii=False, indent=2)

print(f'已从dev.json中提取{len(filtered_data)}个样例，保存到{output_file_path}')
print(f'提取的question_id: {sorted(selected_values)}')


