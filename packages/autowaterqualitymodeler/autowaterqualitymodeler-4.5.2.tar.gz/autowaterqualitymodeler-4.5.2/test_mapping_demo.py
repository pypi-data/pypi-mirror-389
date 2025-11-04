#!/usr/bin/env python3
"""
双向列名映射功能演示脚本
展示输入时标准化，输出时用户友好化的完整流程
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

def demo_column_mapping():
    """演示双向列名映射功能"""
    
    print("=" * 60)
    print("双向列名映射功能演示")
    print("=" * 60)
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 1. 展示支持的映射关系
    print("\n1. 支持的输入映射关系:")
    print("-" * 40)
    input_mappings = config_manager.get_supported_column_names()
    for user_name, standard_name in list(input_mappings.items())[:15]:  # 只显示前15个
        print(f"   {user_name:15} → {standard_name}")
    print(f"   ... 共支持 {len(input_mappings)} 种输入格式")
    
    print("\n2. 输出映射关系:")
    print("-" * 40)
    for standard_name in config_manager.get_water_quality_params():
        output_name = config_manager.format_output_column_name(standard_name)
        print(f"   {standard_name:10} → {output_name}")
    
    # 2. 创建测试数据 - 使用多种格式的列名
    print("\n3. 测试数据准备:")
    print("-" * 40)
    
    # 模拟光谱数据
    wavelengths = np.arange(400, 901, 10)
    n_samples = 5
    spectrum_data = pd.DataFrame(
        np.random.rand(n_samples, len(wavelengths)) * 0.5 + 0.1,
        columns=wavelengths.astype(float)
    )
    print(f"   光谱数据: {spectrum_data.shape[0]} 个样本, {spectrum_data.shape[1]} 个波段")
    
    # 模拟用户数据 - 使用混合格式的列名
    metric_data = pd.DataFrame({
        'TURBIDITY': [10.2, 15.3, 8.7, 12.1, 9.8],        # 大写英文
        '叶绿素a': [25.1, 30.4, 18.9, 22.3, 27.6],         # 中文
        'SS': [12.5, 18.2, 9.8, 14.6, 11.3],              # 大写简写
        'do': [8.5, 7.2, 9.1, 8.8, 7.9],                  # 小写标准名
        'COD': [45.2, 52.1, 38.7, 41.3, 47.8],            # 简写
        'NH3-N': [1.2, 1.8, 0.9, 1.4, 1.1]               # 带分隔符
    })
    
    print("   原始用户数据列名:", metric_data.columns.tolist())
    
    # 3. 演示输入映射过程
    print("\n4. 输入映射过程:")
    print("-" * 40)
    
    for col in metric_data.columns:
        mapped = config_manager.normalize_column_name(col)
        print(f"   {col:15} → {mapped}")
    
    # 应用输入映射
    normalized_data = config_manager.normalize_dataframe_columns(metric_data)
    print(f"\n   标准化后列名: {normalized_data.columns.tolist()}")
    
    # 4. 演示输出映射过程
    print("\n5. 输出映射过程:")
    print("-" * 40)
    
    for col in normalized_data.columns:
        mapped = config_manager.format_output_column_name(col)
        print(f"   {col:10} → {mapped}")
    
    # 应用输出映射
    formatted_data = config_manager.format_output_dataframe_columns(normalized_data)
    print(f"\n   格式化后列名: {formatted_data.columns.tolist()}")
    
    # 5. 展示完整的映射流程
    print("\n6. 完整映射流程总结:")
    print("-" * 40)
    original_cols = metric_data.columns.tolist()
    final_cols = formatted_data.columns.tolist()
    
    for orig, final in zip(original_cols, final_cols):
        # 找到中间的标准名称
        standard = config_manager.normalize_column_name(orig)
        print(f"   {orig:15} → {standard:10} → {final}")
    
    # 6. 展示数据一致性
    print("\n7. 数据一致性验证:")
    print("-" * 40)
    print(f"   原始数据形状: {metric_data.shape}")
    print(f"   标准化数据形状: {normalized_data.shape}")
    print(f"   格式化数据形状: {formatted_data.shape}")
    print(f"   数据值是否一致: {np.allclose(metric_data.values, formatted_data.values)}")
    
    # 7. 显示样本数据
    print("\n8. 数据样本:")
    print("-" * 40)
    print("   原始数据前2行:")
    print(metric_data.head(2).to_string(index=False))
    
    print("\n   最终输出数据前2行:")
    print(formatted_data.head(2).to_string(index=False))
    
    print("\n" + "=" * 60)
    print("双向映射功能演示完成！")
    print("✅ 输入标准化: 支持多种用户输入格式")
    print("✅ 输出用户友好化: 统一的首字母大写简写格式")
    print("✅ 数据一致性: 映射过程不改变数据值")
    print("✅ 配置驱动: 灵活可定制的映射规则")
    print("=" * 60)

if __name__ == "__main__":
    demo_column_mapping()