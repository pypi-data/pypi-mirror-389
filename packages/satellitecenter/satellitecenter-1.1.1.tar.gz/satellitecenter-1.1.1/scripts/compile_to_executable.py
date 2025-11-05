#!/usr/bin/env python3
"""
使用 Nuitka 编译 interface.py 成独立可执行文件

生成的 .exe（Windows）或可执行文件（Linux）可以直接运行，
无需 Python 环境

使用方法：
    uv run python scripts/compile_to_executable.py
"""

import subprocess
import sys
from pathlib import Path


def compile_to_executable() -> None:
    """编译 interface.py 为独立可执行文件"""

    project_root = Path(__file__).parent.parent
    interface_file = project_root / "interface.py"
    output_dir = project_root / "dist_executable"

    if not interface_file.exists():
        print(f"错误：{interface_file} 不存在")
        sys.exit(1)

    output_dir.mkdir(exist_ok=True)

    # 编译选项
    nuitka_args = [
        sys.executable,
        "-m",
        "nuitka",
        "--onefile",  # 生成单个可执行文件
        "--output-dir=" + str(output_dir),
        "--follow-imports",  # 跟踪所有导入
        "--include-package=satellitecenter",  # 包含自己的包
        "--include-package-data=satellitecenter",  # 包含数据文件
        "--remove-output",  # 删除中间文件
        "--quiet",  # 安静模式
        "--jobs=4",  # 4 线程并行编译
        "--lto=auto",  # 启用链接时优化
    ]

    # 如果是 Windows，保留控制台
    if sys.platform == "win32":
        nuitka_args.append("--windows-console-mode=attach")

    nuitka_args.append(str(interface_file))

    print("=" * 80)
    print("🔨 开始编译可执行文件...")
    print(f"源文件：{interface_file}")
    print(f"输出目录：{output_dir}")
    print("=" * 80)
    print("\n这个过程可能需要 2-5 分钟，请耐心等待...\n")

    try:
        result = subprocess.run(nuitka_args, check=True)

        # 确定输出文件名
        if sys.platform == "win32":
            exe_file = output_dir / "interface.exe"
        else:
            exe_file = output_dir / "interface"

        print("\n" + "=" * 80)
        print("✅ 编译成功！")
        print(f"\n生成的可执行文件：{exe_file}")
        print(f"文件大小：{exe_file.stat().st_size / 1024 / 1024:.1f} MB")
        print("=" * 80)

        print("\n使用方法：")
        if sys.platform == "win32":
            print(f"  {exe_file}")
            print("\n或者通过命令行传参：")
            print(f"  {exe_file} --spectrum spectrum.csv --measure measure.csv --save_dir output/")
        else:
            print(f"  ./{exe_file.name}")
            print("\n或者通过命令行传参：")
            print(f"  ./{exe_file.name} --spectrum spectrum.csv --measure measure.csv --save_dir output/")

        print("\n✅ 特点：")
        print("  • 无需 Python 环境")
        print("  • 源码完全隐藏（编译成二进制）")
        print("  • 可直接分发给用户")
        print("=" * 80)

    except subprocess.CalledProcessError as e:
        print(f"\n❌ 编译失败")
        print(f"错误代码：{e.returncode}")
        print("\n请检查：")
        print("1. 是否安装了 C/C++ 编译器（MSVC 或 GCC）")
        print("2. 是否有足够的磁盘空间")
        print("3. 所有依赖是否已安装")
        sys.exit(1)


if __name__ == "__main__":
    compile_to_executable()
