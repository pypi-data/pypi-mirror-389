# -*- coding: utf-8 -*-

"""配置文件加载工具模块"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置文件加载器

    负责加载和缓存 JSON 配置文件，提供统一的配置访问接口。
    支持多个配置文件，避免重复加载。
    """

    _cache: dict[str, dict[str, Any]] = {}

    @classmethod
    def load_config(
        cls,
        config_path: str | Path,
        cache_enabled: bool = True,
    ) -> dict[str, Any]:
        """加载配置文件

        从指定路径加载 JSON 配置文件。支持缓存机制，避免重复读取磁盘。

        Args:
            config_path: 配置文件的绝对或相对路径
            cache_enabled: 是否使用缓存（默认 True）

        Returns:
            解析后的配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: JSON 格式无效
            ValueError: 配置内容无效

        Examples:
            >>> config = ConfigLoader.load_config("config/indicator_mapping.json")
            >>> mapping = config.get("indicator_mapping", {})
        """
        config_path = Path(config_path)

        # 检查缓存
        config_key = str(config_path.resolve())
        if cache_enabled and config_key in cls._cache:
            logger.debug(f"从缓存加载配置: {config_path}")
            return cls._cache[config_key]

        # 验证文件存在
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 验证配置内容非空
            if not isinstance(config, dict):
                raise ValueError(
                    f"配置文件必须是 JSON 对象，而非 {type(config).__name__}"
                )

            if not config:
                raise ValueError("配置文件内容为空")

            # 缓存配置
            if cache_enabled:
                cls._cache[config_key] = config
                logger.debug(f"配置文件已加载并缓存: {config_path}")
            else:
                logger.debug(f"配置文件已加载（缓存关闭）: {config_path}")

            return config

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误 ({config_path}): {e}")
            raise json.JSONDecodeError(
                f"配置文件 JSON 格式无效: {e.msg}",
                e.doc,
                e.pos,
            ) from e

    @classmethod
    def clear_cache(cls) -> None:
        """清空所有缓存配置

        在测试或需要重新加载配置时使用。
        """
        cls._cache.clear()
        logger.debug("配置缓存已清空")

    @classmethod
    def get_config_dir(cls) -> Path:
        """获取配置文件目录

        返回项目中 config 目录的绝对路径。
        该目录位于 src/satellitecenter/config/

        Returns:
            配置目录的 Path 对象
        """
        # 获取当前模块所在的目录
        current_file = Path(__file__)
        config_dir = current_file.parent.parent / "config"

        if not config_dir.exists():
            raise FileNotFoundError(f"配置目录不存在: {config_dir}")

        return config_dir
