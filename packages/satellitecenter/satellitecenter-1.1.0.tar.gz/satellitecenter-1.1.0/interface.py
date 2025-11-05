#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AeroSpot自动化报告生成工具V3 - 运行入口
=====================================

这是主程序的运行入口，用于直接运行该工具。
"""

import os
import sys

# 硬编码缓存配置
CACHE_ENABLED = True  # 修改此处控制是否启用下载缓存

# 将src目录添加到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 导入并运行主程序
from satellitecenter import main

if __name__ == "__main__":
    sys.exit(main())
