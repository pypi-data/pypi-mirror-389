# -*- coding: utf-8 -*-

"""配置文件加载工具模块"""

import json
import logging
from importlib import resources
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
        resource_package: str | None = None,
    ) -> dict[str, Any]:
        """加载配置文件

        优先从文件系统加载配置；当文件不存在且提供了 ``resource_package`` 时，
        会尝试从包资源中读取（支持 Nuitka module 等打包形式）。

        Args:
            config_path: 配置文件的绝对/相对路径或资源文件名
            cache_enabled: 是否使用缓存（默认 True）
            resource_package: 当文件不存在时尝试读取的包名，如 "satellitecenter.config"

        Returns:
            解析后的配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: JSON 格式无效
            ValueError: 配置内容无效
        """

        raw_path = str(config_path)
        path = Path(raw_path)

        if path.exists():
            config_key = str(path.resolve())
            if cache_enabled and config_key in cls._cache:
                logger.debug(f"从缓存加载配置: {config_key}")
                return cls._cache[config_key]

            config = cls._load_from_file(path)

            if cache_enabled:
                cls._cache[config_key] = config
                logger.debug(f"配置文件已加载并缓存: {config_key}")
            else:
                logger.debug(f"配置文件已加载（缓存关闭）: {config_key}")

            return config

        if resource_package:
            return cls._load_from_resource(
                resource_package=resource_package,
                resource_name=raw_path,
                cache_enabled=cache_enabled,
            )

        raise FileNotFoundError(f"配置文件不存在: {path}")

    @classmethod
    def _load_from_file(cls, path: Path) -> dict[str, Any]:
        """从文件系统读取配置"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误 ({path}): {e}")
            raise json.JSONDecodeError(
                f"配置文件 JSON 格式无效: {e.msg}",
                e.doc,
                e.pos,
            ) from e

        cls._validate_config(config)
        return config

    @classmethod
    def _load_from_resource(
        cls,
        resource_package: str,
        resource_name: str,
        cache_enabled: bool,
    ) -> dict[str, Any]:
        """从包资源读取配置文件"""

        resource_key = f"resource://{resource_package}/{resource_name}"
        if cache_enabled and resource_key in cls._cache:
            logger.debug(f"从资源缓存加载配置: {resource_key}")
            return cls._cache[resource_key]

        try:
            package_root = resources.files(resource_package)
        except ModuleNotFoundError as exc:
            raise FileNotFoundError(f"资源包不存在: {resource_package}") from exc

        normalized_name = resource_name.replace("\\", "/")
        path_segments = [segment for segment in normalized_name.split("/") if segment]
        resource = package_root.joinpath(*path_segments)
        if not resource.is_file():
            raise FileNotFoundError(
                f"资源文件不存在: {resource_package}:{resource_name}"
            )

        try:
            data = resource.read_text(encoding="utf-8")
            config = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误 ({resource_key}): {e}")
            raise json.JSONDecodeError(
                f"配置文件 JSON 格式无效: {e.msg}",
                e.doc,
                e.pos,
            ) from e

        cls._validate_config(config)

        if cache_enabled:
            cls._cache[resource_key] = config
            logger.debug(f"资源配置已加载并缓存: {resource_key}")
        else:
            logger.debug(f"资源配置已加载（缓存关闭）: {resource_key}")

        return config

    @staticmethod
    def _validate_config(config: Any) -> None:
        """验证配置内容有效性"""
        if not isinstance(config, dict):
            raise ValueError(
                f"配置文件必须是 JSON 对象，而非 {type(config).__name__}"
            )

        if not config:
            raise ValueError("配置文件内容为空")

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
        若目录未在文件系统中（如 Nuitka module），建议改用 ``load_config``
        并提供 ``resource_package`` 参数。

        Returns:
            配置目录的 Path 对象
        """
        current_file = Path(__file__)
        config_dir = current_file.parent.parent / "config"

        if not config_dir.exists():
            raise FileNotFoundError(
                "配置目录不存在或已被打包为资源，请使用 load_config(..., "
                "resource_package='satellitecenter.config')"
            )

        return config_dir
