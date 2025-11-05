# -*- coding: utf-8 -*-

"""指标标准化工具单元测试"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from satellitecenter.utils import ConfigLoader, IndicatorStandardizer


class TestConfigLoader:
    """ConfigLoader 类的单元测试"""

    def setup_method(self):
        """每个测试前清空缓存"""
        ConfigLoader.clear_cache()

    def test_load_config_success(self, tmp_path: Path):
        """测试成功加载有效的 JSON 配置文件"""
        # 创建临时配置文件
        config_data = {
            "indicator_mapping": {"Turb": ["turbidity", "浊度"]},
            "version": "1.0",
        }
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        # 加载配置
        result = ConfigLoader.load_config(config_file)

        assert result == config_data
        assert result["version"] == "1.0"

    def test_load_config_caching(self, tmp_path: Path):
        """测试配置缓存机制"""
        config_data = {"test": "data"}
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        # 第一次加载
        result1 = ConfigLoader.load_config(config_file, cache_enabled=True)
        # 删除文件
        config_file.unlink()
        # 第二次加载应该从缓存中获取（不会抛异常）
        result2 = ConfigLoader.load_config(config_file, cache_enabled=True)

        assert result1 == result2
        assert result1 == config_data

    def test_load_config_file_not_found(self):
        """测试文件不存在时抛异常"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_config("/nonexistent/config.json")

    def test_load_config_invalid_json(self, tmp_path: Path):
        """测试 JSON 格式无效时抛异常"""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ invalid json }", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            ConfigLoader.load_config(config_file)

    def test_load_config_empty_dict(self, tmp_path: Path):
        """测试空配置字典抛异常"""
        config_file = tmp_path / "empty.json"
        config_file.write_text("{}", encoding="utf-8")

        with pytest.raises(ValueError, match="配置文件内容为空"):
            ConfigLoader.load_config(config_file)

    def test_load_config_not_dict(self, tmp_path: Path):
        """测试非字典 JSON 内容抛异常"""
        config_file = tmp_path / "not_dict.json"
        config_file.write_text('["array", "not", "dict"]', encoding="utf-8")

        with pytest.raises(ValueError, match="必须是 JSON 对象"):
            ConfigLoader.load_config(config_file)

    def test_clear_cache(self, tmp_path: Path):
        """测试清空缓存"""
        config_data = {"test": "data"}
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        # 加载配置到缓存
        ConfigLoader.load_config(config_file, cache_enabled=True)
        assert len(ConfigLoader._cache) > 0

        # 清空缓存
        ConfigLoader.clear_cache()
        assert len(ConfigLoader._cache) == 0


class TestIndicatorStandardizer:
    """IndicatorStandardizer 类的单元测试"""

    def setup_method(self):
        """每个测试前重置单例"""
        IndicatorStandardizer.reload()

    def test_singleton_pattern(self):
        """测试单例模式"""
        std1 = IndicatorStandardizer()
        std2 = IndicatorStandardizer()

        assert std1 is std2

    def test_standardize_column_name_chinese(self):
        """测试中文指标名转换"""
        standardizer = IndicatorStandardizer()

        assert standardizer.standardize_column_name("浊度") == "Turb"
        assert standardizer.standardize_column_name("悬浮物") == "SS"
        assert standardizer.standardize_column_name("溶解氧") == "DO"

    def test_standardize_column_name_english(self):
        """测试英文指标名转换"""
        standardizer = IndicatorStandardizer()

        assert standardizer.standardize_column_name("turbidity") == "Turb"
        assert standardizer.standardize_column_name("suspended solids") == "SS"
        assert standardizer.standardize_column_name("dissolved oxygen") == "DO"

    def test_standardize_column_name_case_insensitive(self):
        """测试大小写不敏感"""
        standardizer = IndicatorStandardizer()

        assert standardizer.standardize_column_name("Turbidity") == "Turb"
        assert standardizer.standardize_column_name("TURBIDITY") == "Turb"
        assert standardizer.standardize_column_name("TuRbIdItY") == "Turb"

    def test_standardize_column_name_unmapped(self):
        """测试未映射的列名返回 None"""
        standardizer = IndicatorStandardizer()

        assert standardizer.standardize_column_name("unknown_indicator") is None
        assert standardizer.standardize_column_name("xyz") is None

    def test_standardize_dataframe_basic(self):
        """测试基本的 DataFrame 标准化"""
        df = pd.DataFrame(
            {"浊度": [1, 2, 3], "turbidity": [4, 5, 6], "溶解氧": [7, 8, 9]}
        )

        standardizer = IndicatorStandardizer()
        result_df, col_names = standardizer.standardize_dataframe(df)

        assert result_df.shape == (3, 3)
        # 注意：列名可能重复，因为"浊度"和"turbidity"都映射到"Turb"
        assert "Turb" in col_names
        assert "DO" in col_names

    def test_standardize_dataframe_keep_unmapped(self):
        """测试保留未映射的列"""
        df = pd.DataFrame({"浊度": [1, 2], "unknown": [3, 4]})

        standardizer = IndicatorStandardizer()
        result_df, col_names = standardizer.standardize_dataframe(
            df, keep_unmapped=True
        )

        assert "Turb" in col_names
        assert "unknown" in col_names

    def test_standardize_dataframe_drop_unmapped(self):
        """测试删除未映射的列"""
        df = pd.DataFrame({"浊度": [1, 2], "unknown": [3, 4]})

        standardizer = IndicatorStandardizer()
        result_df, col_names = standardizer.standardize_dataframe(
            df, keep_unmapped=False
        )

        assert "Turb" in col_names
        assert "unknown" not in col_names
        assert len(col_names) == 1

    def test_standardize_dataframe_empty(self):
        """测试空 DataFrame 返回空结果"""
        df = pd.DataFrame()

        standardizer = IndicatorStandardizer()
        result_df, col_names = standardizer.standardize_dataframe(df)

        assert result_df.empty
        assert col_names == []

    def test_standardize_dataframe_invalid_input(self):
        """测试非 DataFrame 输入抛异常"""
        standardizer = IndicatorStandardizer()

        with pytest.raises(ValueError, match="必须是 pandas DataFrame"):
            standardizer.standardize_dataframe([1, 2, 3])  # type: ignore

    def test_standardize_dataframe_reset_index(self):
        """测试结果 DataFrame 索引是否重置"""
        df = pd.DataFrame({"浊度": [1, 2, 3]}, index=[10, 20, 30])

        standardizer = IndicatorStandardizer()
        result_df, _ = standardizer.standardize_dataframe(df)

        # 索引应该被重置为 0, 1, 2
        assert result_df.index.tolist() == [0, 1, 2]

    def test_reload_clears_cache(self):
        """测试 reload 方法清空缓存"""
        # 创建实例，加载配置
        std1 = IndicatorStandardizer()
        initial_cache_size = len(ConfigLoader._cache)

        # Reload
        IndicatorStandardizer.reload()

        # 缓存应该被清空
        assert len(ConfigLoader._cache) == 0

        # 创建新实例应该重新加载配置
        std2 = IndicatorStandardizer()
        assert std1 is not std2


class TestIntegration:
    """集成测试"""

    def setup_method(self):
        """每个测试前重置单例"""
        IndicatorStandardizer.reload()

    def test_real_world_scenario(self):
        """测试真实场景的数据处理"""
        # 模拟真实的测量数据
        measure_data = pd.DataFrame(
            {
                "日期": ["2024-01-01", "2024-01-02"],
                "浊度": [1.5, 2.3],
                "turbidity": [1.6, 2.4],
                "未知指标": [10, 20],
                "溶解氧": [5.5, 6.2],
            }
        )

        standardizer = IndicatorStandardizer()
        result_df, col_names = standardizer.standardize_dataframe(measure_data)

        # 检查结果
        assert len(col_names) == 5
        assert result_df.shape == (2, 5)
        # 应该包含标准化的指标名
        assert "Turb" in col_names
        assert "DO" in col_names
