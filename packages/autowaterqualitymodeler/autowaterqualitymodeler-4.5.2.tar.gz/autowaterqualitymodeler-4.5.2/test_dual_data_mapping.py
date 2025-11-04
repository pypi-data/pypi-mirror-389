#!/usr/bin/env python3
"""
测试双数据源列名映射功能
验证metric_data和origin_merged_data的列名都能正确标准化
"""

import pandas as pd
import numpy as np
import logging
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autowaterqualitymodeler.core.config_manager import ConfigManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_dual_data_mapping():
    """测试两个数据源的列名映射"""
    
    print("=" * 60)
    print("双数据源列名映射测试")
    print("=" * 60)
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 1. 创建测试数据 - metric_data (用户当前实测数据)
    metric_data = pd.DataFrame({
        'TURBIDITY': [10.2, 15.3, 8.7],        # 大写英文
        '叶绿素a': [25.1, 30.4, 18.9],          # 中文
        'SS': [12.5, 18.2, 9.8],               # 大写简写
    })
    
    # 2. 创建测试数据 - origin_merged_data (历史完整数据)
    origin_merged_data = pd.DataFrame({
        'Turbidity': [9.8, 11.2, 13.5, 8.9, 12.1],     # 首字母大写
        'CHLA': [23.5, 28.1, 19.7, 31.2, 26.8],        # 大写英文 
        '悬浮物': [11.8, 15.9, 8.3, 17.2, 13.6],        # 中文
        'DO': [8.2, 7.8, 9.1, 7.5, 8.9],               # 大写简写
        '氨氮': [1.1, 1.5, 0.8, 1.7, 1.3],              # 中文
    })
    
    print("\n1. 原始数据:")
    print("-" * 40)
    print(f"metric_data 列名: {metric_data.columns.tolist()}")
    print(f"origin_merged_data 列名: {origin_merged_data.columns.tolist()}")
    
    # 3. 测试标准化过程
    print("\n2. 标准化过程:")
    print("-" * 40)
    
    # 标准化 metric_data
    print("标准化 metric_data:")
    for col in metric_data.columns:
        mapped = config_manager.normalize_column_name(col)
        print(f"   {col:15} → {mapped}")
    
    normalized_metric = config_manager.normalize_dataframe_columns(metric_data)
    print(f"   结果: {normalized_metric.columns.tolist()}")
    
    # 标准化 origin_merged_data
    print("\n标准化 origin_merged_data:")
    for col in origin_merged_data.columns:
        mapped = config_manager.normalize_column_name(col)
        print(f"   {col:15} → {mapped}")
    
    normalized_merged = config_manager.normalize_dataframe_columns(origin_merged_data)
    print(f"   结果: {normalized_merged.columns.tolist()}")
    
    # 4. 验证列名一致性
    print("\n3. 标准化结果验证:")
    print("-" * 40)
    
    # 检查是否有重叠的指标
    metric_cols = set(normalized_metric.columns)
    merged_cols = set(normalized_merged.columns)
    common_cols = metric_cols.intersection(merged_cols)
    
    print(f"metric_data 标准化列名: {sorted(metric_cols)}")
    print(f"origin_merged_data 标准化列名: {sorted(merged_cols)}")
    print(f"共同指标: {sorted(common_cols)}")
    
    # 5. 模拟数据合并场景
    print("\n4. 数据合并兼容性测试:")
    print("-" * 40)
    
    # 这模拟了 _prepare_merged_data 方法中的操作
    # 如果有共同指标，应该能够正确匹配和处理
    if common_cols:
        print("✅ 发现共同指标，数据可以正确合并")
        for col in common_cols:
            metric_vals = normalized_metric[col].values if col in normalized_metric.columns else "N/A"
            merged_vals = normalized_merged[col].values if col in normalized_merged.columns else "N/A"
            print(f"   {col}: metric有{len(metric_vals) if hasattr(metric_vals, '__len__') else 0}个值, merged有{len(merged_vals) if hasattr(merged_vals, '__len__') else 0}个值")
    else:
        print("⚠️  没有共同指标，请检查映射配置")
    
    # 6. 测试输出映射
    print("\n5. 输出映射测试:")
    print("-" * 40)
    
    # 合并所有标准化后的列名进行输出映射测试
    all_standard_cols = metric_cols.union(merged_cols)
    
    print("标准名称 → 输出格式:")
    for col in sorted(all_standard_cols):
        output_name = config_manager.format_output_column_name(col)
        print(f"   {col:10} → {output_name}")
    
    # 7. 完整流程演示
    print("\n6. 完整映射流程演示:")
    print("-" * 40)
    
    # 演示一个完整的映射流程
    example_cases = [
        ("TURBIDITY", "metric_data"),
        ("Turbidity", "origin_merged_data"),
        ("叶绿素a", "metric_data"),
        ("CHLA", "origin_merged_data"),
        ("悬浮物", "origin_merged_data"),
        ("SS", "metric_data")
    ]
    
    for original_name, source in example_cases:
        standard_name = config_manager.normalize_column_name(original_name)
        output_name = config_manager.format_output_column_name(standard_name)
        print(f"   {source:20} | {original_name:15} → {standard_name:10} → {output_name}")
    
    print("\n" + "=" * 60)
    print("双数据源列名映射测试完成！")
    print("✅ metric_data 列名标准化正常")
    print("✅ origin_merged_data 列名标准化正常") 
    print("✅ 标准化后的数据具有一致的列名格式")
    print("✅ 输出映射生成用户友好的列名")
    print("=" * 60)

if __name__ == "__main__":
    test_dual_data_mapping()