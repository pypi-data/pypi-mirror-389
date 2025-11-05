# -*- coding: utf-8 -*-
"""SatelliteCenter - 卫星中心自动化建模工具"""

# 版本号获取，优先级：包元数据 > _version.py > fallback
# 解决方案参考：Python 包版本管理最佳实践
try:
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("satellitecenter")
    except PackageNotFoundError:
        # 开发环境或未安装的包，尝试从 _version.py 获取
        try:
            from ._version import __version__
        except ImportError:
            __version__ = "0.1.0"  # fallback 版本
except ImportError:
    # Python < 3.8，使用 importlib_metadata
    try:
        from importlib_metadata import PackageNotFoundError, version

        try:
            __version__ = version("satellitecenter")
        except PackageNotFoundError:
            try:
                from ._version import __version__
            except ImportError:
                __version__ = "0.1.0"
    except ImportError:
        # 完全 fallback
        try:
            from ._version import __version__
        except ImportError:
            __version__ = "0.1.0"

from satellitecenter.main import main

__all__ = [
    "main",
]
