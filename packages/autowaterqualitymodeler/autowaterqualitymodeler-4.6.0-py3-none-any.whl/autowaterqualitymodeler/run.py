"""
AutoWaterQualityModeler 使用示例

这个脚本展示了如何使用 AutoWaterQualityModeler 库来自动构建水质预测模型。
"""

import os
import logging
from autowaterqualitymodeler.core.modeler import AutoWaterQualityModeler

def main(spectrum_data, uav_data, measure_data, matched_idx=None):
    # 获取或配置logger
    # 如果main.py已经配置过日志，则直接使用
    logger = logging.getLogger(__name__)

    logger.info("启动一键式特征排序建模或模型微调程序...")
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"当前目录: {current_dir}")
    
    
    # 加载光谱数据
    spectrum_data.columns = spectrum_data.columns.astype(float)  # 确保列名是波长值

    # 初始化建模器
    try:
        modeler = AutoWaterQualityModeler()
        logger.info("成功初始化AutoWaterQualityModeler")
    except Exception as e:
        logger.error(f"初始化建模器失败: {e}", exc_info=True)
        return
    
    # 指定数据类型并一键建模
    try:
        # 执行建模
        result = modeler.fit(
            spectrum_data=spectrum_data,
            origin_merged_data=uav_data,
            metric_data=measure_data,
            matched_idx=matched_idx,
            data_type="aerospot"
        )
        
        # 【新增】应用输出列名映射
        config_manager = modeler.config_manager
        
        # 格式化预测结果的列名
        formatted_predictions = config_manager.format_output_dataframe_columns(
            result.predictions
        )
        
        # 格式化全部预测结果的列名（如果存在）
        formatted_all_predictions = None
        if result.has_all_predictions():
            formatted_all_predictions = config_manager.format_output_dataframe_columns(
                result.all_predictions
            )
        
        logger.info("已完成输出列名格式化")
        
        # 转换为兼容旧接口的格式
        if formatted_all_predictions is not None:
            return result.models, formatted_predictions, formatted_all_predictions
        else:
            return result.models, formatted_predictions
        
    except Exception as e:
        logger.error(f"建模过程出错: {e}", exc_info=True)
        return {}