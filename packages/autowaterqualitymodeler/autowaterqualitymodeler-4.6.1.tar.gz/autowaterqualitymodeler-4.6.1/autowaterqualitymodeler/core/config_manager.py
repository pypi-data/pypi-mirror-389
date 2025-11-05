"""
配置管理模块，提供特征/系统配置的加载和访问功能（支持 .py/.json）
"""

import json
import os
import logging
import importlib
import importlib.util
from types import ModuleType
from typing import Any
from .exceptions import ConfigurationError, FileOperationError

# 获取模块日志记录器
logger = logging.getLogger(__name__)


def _load_module_from_path(path: str) -> ModuleType:
    """按路径动态加载 Python 模块（不加入 sys.modules 命名冲突最小化）。"""
    spec = importlib.util.spec_from_file_location("awqm_user_config", path)
    if spec is None or spec.loader is None:
        raise FileOperationError(f"无法加载配置模块: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_config_from_module(module_name: str, attr_candidates: list[str]) -> dict:
    """从模块名加载并读取给定候选属性中的第一个字典。

    Args:
        module_name: 模块的导入路径
        attr_candidates: 可能的配置变量名按优先级排列

    Returns:
        dict: 配置字典
    """
    module = importlib.import_module(module_name)
    for attr in attr_candidates:
        cfg = getattr(module, attr, None)
        if isinstance(cfg, dict):
            return cfg
    raise ConfigurationError(
        f"模块 {module_name} 未找到有效配置变量: {attr_candidates}"
    )


class ConfigManager:
    """配置管理器，处理特征/系统配置文件加载和访问"""

    # 默认支持的数据类型
    DATA_TYPES = ["warning_device", "shore_data", "smart_water", "aerospot"]

    def __init__(self, config_path: str | None = None, system_config_path: str | None = None):
        """
        初始化配置管理器

        Args:
            config_path: 特征配置文件路径；默认使用 config/features_config.py
            system_config_path: 系统配置文件路径；默认使用 config/system_config.py
        """
        # 加载特征配置（默认通过包内导入，避免文件系统依赖）
        if config_path is None:
            # 包内固定模块导入
            self.config_path = 'autowaterqualitymodeler.config.features_config'
            self.config = _load_config_from_module(
                self.config_path,
                ["CONFIG", "FEATURES_CONFIG", "config"],
            )
            logger.info(f"成功通过模块导入特征配置: {self.config_path}")
        else:
            # 兼容：传入为模块名/JSON/文件路径
            self.config_path = config_path
            self.config = self._load_config(config_path)

        # 加载系统配置（默认通过包内导入，若失败则使用默认配置）
        if system_config_path is None:
            try:
                self.system_config_path = 'autowaterqualitymodeler.config.system_config'
                self.system_config = _load_config_from_module(
                    self.system_config_path, ["SYSTEM_CONFIG", "CONFIG", "config"]
                )
                logger.info(f"成功通过模块导入系统配置: {self.system_config_path}")
            except Exception:
                logger.info("包内系统配置导入失败，回退到默认系统配置")
                self.system_config_path = None
                self.system_config = self._get_default_system_config()
        else:
            self.system_config_path = system_config_path
            self.system_config = self._load_system_config(system_config_path)

        # 加载列名映射配置
        self._input_mapping = self._load_input_mapping()
        self._output_mapping = self._load_output_mapping()
    
    def _load_config(self, config_path: str) -> dict:
        """
        加载特征配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict: 加载的配置对象
            
        Raises:
            FileOperationError: 文件读取失败时
            ConfigurationError: 配置文件格式错误时
        """
        # 支持三种输入：模块名、.py/.json 路径、JSON 路径
        if not os.path.exists(config_path):
            # 尝试按模块名导入（适配传入模块路径的场景）
            try:
                config = _load_config_from_module(
                    config_path, ["CONFIG", "FEATURES_CONFIG", "config"]
                )
                logger.info(f"成功通过模块名加载特征配置: {config_path}")
            except Exception as e:
                raise FileOperationError(
                    f"配置不存在且模块导入失败: {config_path}",
                    {"file_path": config_path, "error": str(e)}
                )
        else:
            _, ext = os.path.splitext(config_path.lower())
            if ext == ".py":
                # 从 Python 模块加载
                try:
                    module = _load_module_from_path(config_path)
                    config = (
                        getattr(module, "CONFIG", None)
                        or getattr(module, "FEATURES_CONFIG", None)
                        or getattr(module, "config", None)
                    )
                except Exception as e:
                    raise FileOperationError(
                        f"加载Python配置模块失败: {config_path}",
                        {"file_path": config_path, "error": str(e)}
                    )
            else:
                # 回退：JSON
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except json.JSONDecodeError as e:
                    raise ConfigurationError(
                        f"配置文件JSON格式错误: {config_path}",
                        {"file_path": config_path, "error": str(e)}
                    )
                except IOError as e:
                    raise FileOperationError(
                        f"读取配置文件失败: {config_path}",
                        {"file_path": config_path, "error": str(e)}
                    )
        
        # 验证配置文件格式
        if not isinstance(config, dict):
            raise ConfigurationError(
                "配置文件根元素必须是字典类型",
                {"file_path": config_path, "actual_type": type(config).__name__}
            )
            
        # 检查必需的数据类型
        missing_types = [dt for dt in self.DATA_TYPES if dt not in config]
        if missing_types:
            logger.warning(f"配置文件中缺少以下数据类型: {missing_types}")
            # 为缺失类型创建空配置
            for dt in missing_types:
                config[dt] = {}
                
        logger.info(f"成功加载特征配置: {config_path}")
        return config
    
    def _load_system_config(self, config_path: str) -> dict:
        """
        加载系统配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict: 加载的系统配置对象
            
        Raises:
            FileOperationError: 文件读取失败时
            ConfigurationError: 配置文件格式错误时
        """
        # 系统配置文件是可选的，如果不存在则尝试按模块名导入，否则使用默认配置
        if not os.path.exists(config_path):
            try:
                system_config = _load_config_from_module(
                    config_path, ["SYSTEM_CONFIG", "CONFIG", "config"]
                )
                logger.info(f"成功通过模块名加载系统配置: {config_path}")
            except Exception:
                logger.info(f"系统配置不存在或模块导入失败: {config_path}，使用默认配置")
                return self._get_default_system_config()
        else:
            _, ext = os.path.splitext(config_path.lower())
            if ext == ".py":
                try:
                    module = _load_module_from_path(config_path)
                    system_config = (
                        getattr(module, "SYSTEM_CONFIG", None)
                        or getattr(module, "CONFIG", None)
                        or getattr(module, "config", None)
                    )
                except Exception:
                    logger.warning(f"系统配置Python模块加载失败: {config_path}，使用默认配置")
                    return self._get_default_system_config()
            else:
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        system_config = json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"系统配置文件JSON格式错误: {config_path}，使用默认配置")
                    return self._get_default_system_config()
                except IOError:
                    logger.warning(f"读取系统配置文件失败: {config_path}，使用默认配置")
                    return self._get_default_system_config()

        if not isinstance(system_config, dict):
            logger.warning("系统配置文件根元素必须是字典类型，使用默认配置")
            return self._get_default_system_config()

        logger.info(f"成功加载系统配置: {config_path}")
        return system_config
    
    def _get_default_system_config(self) -> dict:
        """获取默认系统配置"""
        return {
            "system": {
                "encryption": {
                    "password": "water_quality_analysis_key",
                    "salt": "water_quality_salt",
                    "enabled": False
                },
                "cache": {
                    "enabled": True,
                    "ttl": 3600,
                    "max_size": 1000
                },
                "parallel": {
                    "enabled": True,
                    "max_workers": 4
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "water_quality_params": [
                "turbidity", "ss", "sd", "do", "codmn", 
                "codcr", "chla", "tn", "tp", "chroma", "nh3n"
            ],
            "feature_stations": [f"STZ{i}" for i in range(1, 20)]
        }
    
    def get_system_config(self, *keys) -> Any:
        """
        获取系统配置值
        
        Args:
            *keys: 配置键的路径，例如 ('system', 'encryption', 'password')
            
        Returns:
            Any: 配置值，如果键不存在则返回None
        """
        config = self.system_config
        for key in keys:
            if isinstance(config, dict) and key in config:
                config = config[key]
            else:
                return None
        return config
    
    def get_water_quality_params(self) -> list[str]:
        """
        获取水质参数列表
        
        Returns:
            List[str]: 水质参数名称列表
        """
        params = self.get_system_config("water_quality_params")
        return params if isinstance(params, list) else []
    
    def get_feature_stations(self) -> list[str]:
        """
        获取特征站点列表
        
        Returns:
            List[str]: 特征站点名称列表
        """
        stations = self.get_system_config("feature_stations")
        return stations if isinstance(stations, list) else []
    
    def get_feature_definitions(self, data_type: str, metric_name: str) -> list[dict]:
        """
        获取指定数据类型和指标的特征定义
        
        Args:
            data_type: 数据类型，必须是DATA_TYPES中的一种
            metric_name: 指标名称
            
        Returns:
            List[Dict]: 特征定义列表
            
        Raises:
            ConfigurationError: 数据类型无效时
        """
        if data_type not in self.DATA_TYPES:
            logger.warning(f"不支持的数据类型: {data_type}")
            return []
            
        # 尝试获取数据类型下的指标特征
        if data_type in self.config and metric_name in self.config[data_type]:
            features = self.config[data_type][metric_name].get("features", [])
            logger.debug(f"找到 {data_type} 下 {metric_name} 指标的 {len(features)} 个特征定义")
        elif data_type in self.config and "default" in self.config[data_type]:
            features = self.config[data_type]["default"].get("features", [])
            logger.debug(f"{data_type} 下 {metric_name} 指标采用默认的 {len(features)} 个特征")
        else:
            logger.warning(f"未找到 {data_type} 下 {metric_name} 指标的特征定义")
            return []
        
        # 获取完整的特征定义
        full_definitions = []
        for ref in features:
            if "feature_id" not in ref:
                logger.warning(f"特征引用缺少feature_id: {ref}")
                continue
                
            feature_id = ref["feature_id"]
            
            # 获取基础特征定义
            if "features" in self.config and feature_id in self.config["features"]:
                base_definition = self.config["features"][feature_id].copy()
                
                # 如果有自定义波段映射，则合并
                if "bands" in ref:
                    base_definition["bands"] = ref["bands"]
                    
                full_definitions.append(base_definition)
            else:
                logger.warning(f"未找到特征ID为 {feature_id} 的定义")
        
        return full_definitions

    def get_model_params(self, data_type: str | None = None, metric_name: str | None = None) -> dict:
        """
        获取模型参数，根据优先级依次尝试：指标级别 > 数据类型级别 > 全局级别
        
        Args:
            data_type: 数据类型，如果为None则只返回全局参数
            metric_name: 指标名称，如果为None则返回数据类型级别的参数
            
        Returns:
            Dict: 合并后的模型参数
        """
        model_params = {}
        
        # 1. 获取全局模型参数（最低优先级）
        global_params = self.config.get("model_params", {})
        model_params.update(global_params)
        
        # 2. 获取数据类型级别的模型参数（中等优先级）
        if data_type and data_type in self.config:
            data_type_params = self.config[data_type].get("model_params", {})
            if data_type_params:
                model_params.update(data_type_params)
        
        # 3. 获取指标级别的模型参数（最高优先级）
        if data_type and metric_name and data_type in self.config and metric_name in self.config[data_type]:
            metric_params = self.config[data_type][metric_name].get("model_params", {})
            if metric_params:
                model_params.update(metric_params)
        
        return model_params
    
    def get_supported_metrics(self, data_type: str) -> list[str]:
        """
        获取指定数据类型支持的指标列表
        
        Args:
            data_type: 数据类型
            
        Returns:
            List[str]: 支持的指标列表
        """
        if data_type not in self.DATA_TYPES:
            logger.warning(f"不支持的数据类型: {data_type}")
            return []
            
        if data_type in self.config:
            # 过滤掉model_params键，它不是指标
            metrics = [key for key in self.config[data_type].keys() if key != "model_params"]
            return metrics
        
        return []
    
    def _load_input_mapping(self) -> dict:
        """加载输入列名映射配置"""
        try:
            mapping_config = self.system_config.get("column_name_mapping", {})
            mappings = mapping_config.get("input_mappings", {})
            
            # 添加标准名称到自身的映射（保持向后兼容）
            for param in self.get_water_quality_params():
                if param not in mappings:
                    mappings[param] = param
                    
            logger.info(f"已加载 {len(mappings)} 个输入列名映射")
            return mappings
        except Exception as e:
            logger.warning(f"加载输入列名映射失败: {e}")
            return {}
    
    def _load_output_mapping(self) -> dict:
        """加载输出列名映射配置"""
        try:
            mapping_config = self.system_config.get("column_name_mapping", {})
            mappings = mapping_config.get("output_mappings", {})
            
            # 如果没有配置输出映射，默认使用首字母大写
            if not mappings:
                for param in self.get_water_quality_params():
                    mappings[param] = param.capitalize()
            
            logger.info(f"已加载 {len(mappings)} 个输出列名映射")
            return mappings
        except Exception as e:
            logger.warning(f"加载输出列名映射失败: {e}")
            # 默认使用首字母大写
            return {param: param.capitalize() 
                    for param in self.get_water_quality_params()}
    
    def normalize_column_name(self, column_name: str) -> str:
        """输入映射：将用户列名标准化为系统内部名称
        
        Args:
            column_name: 用户提供的列名
            
        Returns:
            str: 标准化后的列名，如果无映射则返回原名称
        """
        return self._input_mapping.get(column_name, column_name)
    
    def format_output_column_name(self, standard_name: str) -> str:
        """输出映射：将系统标准名称转换为用户友好名称
        
        Args:
            standard_name: 系统内部标准名称
            
        Returns:
            str: 用户友好的列名
        """
        return self._output_mapping.get(standard_name, standard_name)
    
    def normalize_dataframe_columns(self, df):
        """标准化DataFrame的列名（输入处理）
        
        Args:
            df: 输入DataFrame
            
        Returns:
            DataFrame: 列名标准化后的DataFrame
        """
        import pandas as pd
        
        normalized_df = df.copy()
        
        column_mapping = {}
        for col in normalized_df.columns:
            normalized_name = self.normalize_column_name(col)
            if normalized_name != col:
                column_mapping[col] = normalized_name
                
        if column_mapping:
            normalized_df = normalized_df.rename(columns=column_mapping)
            logger.info(f"输入列名映射: {column_mapping}")
            
        return normalized_df
    
    def format_output_dataframe_columns(self, df):
        """格式化DataFrame的列名（输出处理）
        
        Args:
            df: 输入DataFrame
            
        Returns:
            DataFrame: 列名格式化后的DataFrame
        """
        import pandas as pd
        
        if df is None or df.empty:
            return df
            
        formatted_df = df.copy()
        
        column_mapping = {}
        for col in formatted_df.columns:
            formatted_name = self.format_output_column_name(col)
            if formatted_name != col:
                column_mapping[col] = formatted_name
                
        if column_mapping:
            formatted_df = formatted_df.rename(columns=column_mapping)
            logger.info(f"输出列名映射: {column_mapping}")
            
        return formatted_df
    
    def get_supported_column_names(self) -> dict:
        """获取所有支持的列名及其映射
        
        Returns:
            dict: {用户列名: 标准列名} 的映射字典
        """
        return self._input_mapping.copy() 
