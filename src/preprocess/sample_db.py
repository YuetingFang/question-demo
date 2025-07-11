#!/usr/bin/env python3
"""
从data/dev.json中随机采样指定数量的样例。
按照特定的难度分布选择样例: simple 30%, moderate 60%, challenging 10%
"""

import json
import random
import argparse
from pathlib import Path
from typing import Dict, List, Any
import os

# 配置
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_INPUT_PATH = BASE_DIR / "data/dev.json"
DEFAULT_OUTPUT_PATH = BASE_DIR / "results/preprocess/sampled_debit_card.json"
DEFAULT_DB_ID = "debit_card_specializing"
DEFAULT_TOTAL_SAMPLES = 20
DEFAULT_DISTRIBUTION = {
    "simple": 0.3,
    "moderate": 0.6,
    "challenging": 0.1
}


def load_data(input_path: Path) -> List[Dict[str, Any]]:
    """
    加载JSON数据
    
    Args:
        input_path: 输入文件路径
        
    Returns:
        加载的JSON数据
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def filter_by_db_id(data: List[Dict[str, Any]], db_id: str) -> List[Dict[str, Any]]:
    """
    过滤指定db_id的样例
    
    Args:
        data: 原始数据
        db_id: 要筛选的数据库ID
        
    Returns:
        筛选后的样例列表
    """
    filtered_data = [item for item in data if item.get('db_id') == db_id]
    print(f"找到 {len(filtered_data)} 个 db_id 为 '{db_id}' 的样例")
    return filtered_data


def group_by_difficulty(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    按照难度级别对样例进行分组
    
    Args:
        data: 原始数据列表
        
    Returns:
        按难度分组的字典
    """
    grouped_data = {
        "simple": [],
        "moderate": [],
        "challenging": []
    }
    
    for item in data:
        difficulty = item.get('difficulty', '')
        if difficulty in grouped_data:
            grouped_data[difficulty].append(item)
    
    return grouped_data


def sample_by_distribution(
    grouped_data: Dict[str, List[Dict[str, Any]]],
    total_samples: int,
    distribution: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    按照指定分布随机采样
    
    Args:
        grouped_data: 按难度分组的数据
        total_samples: 要采样的总数量
        distribution: 采样分布 {'simple': 0.3, 'moderate': 0.6, 'challenging': 0.1}
        
    Returns:
        采样后的样例列表
    """
    sampled_data = []
    
    # 计算每个难度级别需要采样的数量
    sample_counts = {}
    for difficulty, ratio in distribution.items():
        count = int(total_samples * ratio)
        if count == 0 and ratio > 0:
            count = 1  # 确保每个非零比例至少有一个样例
        sample_counts[difficulty] = count
    
    # 调整总数量以匹配要求
    total_count = sum(sample_counts.values())
    if total_count < total_samples:
        # 如果总数不足，将剩余的分配给moderate
        sample_counts['moderate'] += (total_samples - total_count)
    
    # 随机采样
    for difficulty, count in sample_counts.items():
        available = grouped_data.get(difficulty, [])
        if not available:
            continue
        
        # 如果可用样例数量少于要求采样数量，全部使用
        if len(available) <= count:
            sampled = available
        else:
            sampled = random.sample(available, count)
        
        sampled_data.extend(sampled)
    
    return sampled_data


def save_data(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    保存数据到JSON文件
    
    Args:
        data: 要保存的数据
        output_path: 输出文件路径
    """
    # 按 question_id 排序
    data_sorted = sorted(data, key=lambda x: x.get('question_id', ''))
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data_sorted, f, ensure_ascii=False, indent=2)
    


def main():
    parser = argparse.ArgumentParser(description='从data/dev.json中随机采样样例')
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT_PATH,
                       help=f'输入文件路径 (默认: {DEFAULT_INPUT_PATH})')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT_PATH,
                       help=f'输出文件路径 (默认: {DEFAULT_OUTPUT_PATH})')
    parser.add_argument('--db_id', type=str, default=DEFAULT_DB_ID,
                       help=f'要筛选的数据库ID (默认: {DEFAULT_DB_ID})')
    parser.add_argument('--samples', type=int, default=DEFAULT_TOTAL_SAMPLES,
                       help=f'要采样的总数量 (默认: {DEFAULT_TOTAL_SAMPLES})')
    parser.add_argument('--simple', type=float, default=DEFAULT_DISTRIBUTION['simple'],
                       help=f"simple难度的比例 (默认: {DEFAULT_DISTRIBUTION['simple']})")
    parser.add_argument('--moderate', type=float, default=DEFAULT_DISTRIBUTION['moderate'],
                       help=f"moderate难度的比例 (默认: {DEFAULT_DISTRIBUTION['moderate']})")
    parser.add_argument('--challenging', type=float, default=DEFAULT_DISTRIBUTION['challenging'],
                       help=f"challenging难度的比例 (默认: {DEFAULT_DISTRIBUTION['challenging']})")
    parser.add_argument('--seed', type=int, default=7,
                       help='随机数种子，用于结果可重复 (默认: 随机)')
    
    args = parser.parse_args()
    

    # 构造分布字典
    distribution = {
        "simple": args.simple,
        "moderate": args.moderate,
        "challenging": args.challenging
    }
    
    # 检查分布和总和
    total_ratio = sum(distribution.values())
    if abs(total_ratio - 1.0) > 0.001:
        # 归一化
        for difficulty in distribution:
            distribution[difficulty] /= total_ratio
    
    # 加载数据
    data = load_data(args.input)
    
    # 筛选指定db_id的样例
    filtered_data = filter_by_db_id(data, args.db_id)
    if not filtered_data:
        print(f"错误: 未找到db_id为'{args.db_id}'的样例")
        return
    
    # 按难度分组
    grouped_data = group_by_difficulty(filtered_data)
    
    # 按分布采样
    sampled_data = sample_by_distribution(grouped_data, args.samples, distribution)
    
    # 保存结果
    save_data(sampled_data, args.output)
    
    # 输出最终分布情况
    final_grouped = group_by_difficulty(sampled_data)
    for difficulty, items in final_grouped.items():
        print(f"难度 '{difficulty}': {len(items)} 个样例 ({len(items)/len(sampled_data):.1%})")


if __name__ == "__main__":
    main()
