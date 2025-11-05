# -*- coding: utf-8 -*-

"""波段名格式化测试"""

import pandas as pd
import pytest

from satellitecenter.main import format_band_name


class TestFormatBandName:
    """format_band_name 函数的单元测试"""

    def test_format_band_name_string_columns(self):
        """测试字符串列名转换为数字"""
        df = pd.DataFrame({"400": [1.0, 2.0], "405": [3.0, 4.0], "410": [5.0, 6.0]})

        result = format_band_name(df)

        # 检查列名是否转换为浮点数
        assert result.columns.tolist() == [400.0, 405.0, 410.0]
        # 检查数据是否保持不变
        assert result.shape == (2, 3)

    def test_format_band_name_numeric_columns(self):
        """测试已是数字的列名"""
        df = pd.DataFrame({400: [1.0, 2.0], 405: [3.0, 4.0], 410: [5.0, 6.0]})

        result = format_band_name(df)

        # 列名应该保持为数字类型
        assert result.columns.tolist() == [400, 405, 410]

    def test_format_band_name_mixed_columns(self):
        """测试字符串和数字混合列名"""
        df = pd.DataFrame({"400": [1.0, 2.0], 405: [3.0, 4.0], "410.5": [5.0, 6.0]})

        result = format_band_name(df)

        # 所有列名应该转换为浮点数
        numeric_cols = [col for col in result.columns if isinstance(col, (int, float))]
        assert len(numeric_cols) == 3

    def test_format_band_name_float_strings(self):
        """测试浮点数字符串列名"""
        df = pd.DataFrame(
            {"400.0": [1.0, 2.0], "405.5": [3.0, 4.0], "410.2": [5.0, 6.0]}
        )

        result = format_band_name(df)

        # 列名应该转换为浮点数
        assert result.columns.tolist() == [400.0, 405.5, 410.2]

    def test_format_band_name_partially_convertible(self):
        """测试部分列名无法转换的情况"""
        df = pd.DataFrame(
            {"400": [1.0, 2.0], "wavelength": [3.0, 4.0], "405": [5.0, 6.0]}
        )

        result = format_band_name(df)

        # 应该成功转换数字列，保留非数字列
        numeric_cols = [col for col in result.columns if isinstance(col, (int, float))]
        assert len(numeric_cols) == 2
        assert "wavelength" in result.columns

    def test_format_band_name_all_non_numeric_fails(self):
        """测试所有列名都无法转换时抛异常"""
        df = pd.DataFrame({"wavelength": [1.0, 2.0], "band": [3.0, 4.0]})

        with pytest.raises(ValueError, match="未能将任何列名转换为数字类型"):
            format_band_name(df)

    def test_format_band_name_empty_dataframe(self):
        """测试空 DataFrame"""
        df = pd.DataFrame()

        result = format_band_name(df)

        assert result.empty

    def test_format_band_name_invalid_input(self):
        """测试非 DataFrame 输入"""
        with pytest.raises(ValueError, match="输入必须是 pandas DataFrame"):
            format_band_name([1, 2, 3])  # type: ignore

    def test_format_band_name_large_wavelength_range(self):
        """测试真实光谱波长范围 (400-2500 nm)"""
        wavelengths = [str(400 + i * 5) for i in range(451)]
        data = {wl: [1.0] * 10 for wl in wavelengths}
        df = pd.DataFrame(data)

        result = format_band_name(df)

        # 检查波段范围
        numeric_cols = sorted(
            [col for col in result.columns if isinstance(col, (int, float))]
        )
        assert numeric_cols[0] == 400.0
        assert numeric_cols[-1] == 2650.0
        assert len(numeric_cols) == 451

    def test_format_band_name_preserves_data(self):
        """测试数据完整性"""
        df = pd.DataFrame({"400": [1.5, 2.5, 3.5], "405": [4.5, 5.5, 6.5]})

        result = format_band_name(df)

        # 检查数据是否保持不变
        assert result[400.0].tolist() == [1.5, 2.5, 3.5]
        assert result[405.0].tolist() == [4.5, 5.5, 6.5]

    def test_format_band_name_column_order(self):
        """测试列顺序是否保持"""
        df = pd.DataFrame({"410": [1.0], "400": [2.0], "405": [3.0]})

        result = format_band_name(df)

        # 列顺序应该保持原样
        assert result.columns.tolist() == [410.0, 400.0, 405.0]
