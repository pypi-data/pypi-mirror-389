# -*- coding: utf-8 -*-

"""指标名称标准化工具模块"""

import logging
from typing import Any, Optional

import pandas as pd

from satellitecenter.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class IndicatorStandardizer:
    """指标名称标准化器

    负责将各种格式的指标名称统一转换为标准名称。
    支持大小写不敏感匹配，使用配置文件管理映射关系。

    Attributes:
        _mapping: 标准指标名到别名列表的映射字典
        _reverse_mapping: 别名到标准指标名的反向映射字典
    """

    _instance: Optional["IndicatorStandardizer"] = None
    _mapping: dict[str, list[str]] = {}
    _reverse_mapping: dict[str, str] = {}

    def __new__(cls) -> "IndicatorStandardizer":
        """实现单例模式，确保只加载一次配置文件"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """初始化指标标准化器

        从配置文件加载映射关系并构建反向映射字典。
        """
        try:
            config = self._load_mapping_config()

            # 提取指标映射关系
            self._mapping = config.get("indicator_mapping", {})

            if not self._mapping:
                logger.warning("指标映射配置为空，使用默认空映射")
                return

            # 构建反向映射：别名 -> 标准指标名
            self._reverse_mapping = {}
            for standard_name, aliases in self._mapping.items():
                for alias in aliases:
                    # 转换为小写，便于大小写不敏感匹配
                    alias_lower = alias.lower()
                    if alias_lower in self._reverse_mapping:
                        logger.warning(
                            f"指标别名冲突: '{alias}' 同时映射到 "
                            f"'{self._reverse_mapping[alias_lower]}' "
                            f"和 '{standard_name}'，使用第一个映射"
                        )
                    else:
                        self._reverse_mapping[alias_lower] = standard_name

            logger.info(
                f"指标标准化器已初始化，共加载 {len(self._mapping)} 个标准指标，"
                f"{len(self._reverse_mapping)} 条映射规则"
            )

        except Exception as e:
            logger.error(f"初始化指标标准化器失败: {e}")
            raise

    def _load_mapping_config(self) -> dict[str, Any]:
        """加载指标映射配置

        优先查找 JSON 文件（便于开发环境覆盖），否则从 Python 模块
        ``satellitecenter.config.indicator_mapping`` 中读取。
        """

        try:
            config_dir = ConfigLoader.get_config_dir()
        except FileNotFoundError:
            config_dir = None

        if config_dir is not None:
            json_path = config_dir / "indicator_mapping.json"
            if json_path.exists():
                return ConfigLoader.load_config(json_path)

        try:
            from satellitecenter.config import indicator_mapping as mapping_module
        except ModuleNotFoundError as exc:
            raise FileNotFoundError(
                "指标映射模块缺失: satellitecenter.config.indicator_mapping"
            ) from exc

        config = getattr(mapping_module, "CONFIG", None)
        if not isinstance(config, dict):
            indicator_mapping = getattr(mapping_module, "INDICATOR_MAPPING", None)
            if not isinstance(indicator_mapping, dict):
                raise ValueError("indicator_mapping 模块缺少 INDICATOR_MAPPING 配置")

            config = {
                "indicator_mapping": indicator_mapping,
                "description": getattr(mapping_module, "DESCRIPTION", ""),
                "version": getattr(mapping_module, "VERSION", ""),
            }

        return config

    def standardize_column_name(self, column_name: str) -> Optional[str]:
        """将单个列名标准化为标准指标名

        使用大小写不敏感匹配，如果找不到映射则返回 None。

        Args:
            column_name: 原始列名（可能是别名或标准名）

        Returns:
            标准指标名，或 None（若列名未在映射中找到）

        Examples:
            >>> standardizer = IndicatorStandardizer()
            >>> standardizer.standardize_column_name("浊度")
            'Turb'
            >>> standardizer.standardize_column_name("turbidity")
            'Turb'
            >>> standardizer.standardize_column_name("UNKNOWN")
            None
        """
        column_lower = column_name.lower()
        standard_name = self._reverse_mapping.get(column_lower)

        if standard_name:
            logger.debug(f"列名 '{column_name}' 映射到标准指标 '{standard_name}'")
        else:
            logger.debug(f"列名 '{column_name}' 未找到映射，保持原名")

        return standard_name

    def standardize_dataframe(
        self,
        data: pd.DataFrame,
        keep_unmapped: bool = True,
    ) -> tuple[pd.DataFrame, list[str]]:
        """标准化 DataFrame 的列名

        将 DataFrame 中的所有列名转换为标准指标名。
        未映射的列可以选择保留（转为小写）或删除。

        Args:
            data: 输入的 DataFrame
            keep_unmapped: 是否保留未映射的列（默认 True）
                           如果为 True，未映射列转为小写并保留
                           如果为 False，未映射列被删除

        Returns:
            tuple[pd.DataFrame, list[str]]:
                - 重命名后的 DataFrame（已重置索引）
                - 标准化后的列名列表

        Raises:
            ValueError: 输入不是有效的 DataFrame

        Examples:
            >>> df = pd.DataFrame({"浊度": [1, 2], "unknown": [3, 4]})
            >>> standardizer = IndicatorStandardizer()
            >>> std_df, cols = standardizer.standardize_dataframe(df)
            >>> std_df.columns.tolist()
            ['Turb', 'unknown']
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError(f"输入必须是 pandas DataFrame，而非 {type(data).__name__}")

        if data.empty:
            logger.warning("输入 DataFrame 为空")
            return pd.DataFrame(), []

        rename_mapping: dict[str, str] = {}
        standardized_columns: list[str] = []

        for col in data.columns.tolist():
            standard_name = self.standardize_column_name(col)

            if standard_name:
                # 找到映射
                rename_mapping[col] = standard_name
                standardized_columns.append(standard_name)
            else:
                # 未找到映射
                if keep_unmapped:
                    # 转为小写并保留
                    col_lower = col.lower()
                    rename_mapping[col] = col_lower
                    standardized_columns.append(col_lower)
                # 如果 keep_unmapped=False，则跳过（不添加到列表）

        # 重命名列
        data_renamed = data.rename(columns=rename_mapping)

        # 删除未映射的列（如果 keep_unmapped=False）
        if not keep_unmapped:
            data_renamed = data_renamed[
                [col for col in data_renamed.columns if col in standardized_columns]
            ]
            standardized_columns = [
                col for col in standardized_columns if col is not None
            ]

        logger.info(
            f"DataFrame 标准化完成，共 {len(data.columns)} 列 → {len(standardized_columns)} 列，"
            f"标准化列名: {', '.join(standardized_columns)}"
        )

        return data_renamed.reset_index(drop=True), standardized_columns

    @classmethod
    def reload(cls) -> None:
        """重新加载配置并重新初始化

        在配置文件更新后使用该方法。
        """
        cls._instance = None
        ConfigLoader.clear_cache()
        logger.info("指标标准化器已重置，将在下次使用时重新加载配置")
