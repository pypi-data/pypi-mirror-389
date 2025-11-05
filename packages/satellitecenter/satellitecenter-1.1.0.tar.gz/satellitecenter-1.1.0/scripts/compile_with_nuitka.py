#!/usr/bin/env python3
"""
使用 Nuitka 编译 SatelliteCenter 包成二进制文件

此脚本逐个编译 src/satellitecenter 包中的所有 Python 文件为编译后的模块
生成的 .pyd 文件放在 dist_compiled/satellitecenter 目录下，保留原有包结构

使用方法：
    uv run python scripts/compile_with_nuitka.py
"""

import shutil
import subprocess
import sys
from pathlib import Path


def compile_package() -> None:
    """编译 satellitecenter 包为二进制模块"""

    project_root = Path(__file__).parent.parent
    src_package = project_root / "src" / "satellitecenter"
    output_base = project_root / "dist_compiled"
    output_package = output_base / "satellitecenter"

    if not src_package.exists():
        print(f"错误：源目录 {src_package} 不存在")
        sys.exit(1)

    # 创建输出目录结构
    output_base.mkdir(exist_ok=True)
    output_package.mkdir(exist_ok=True)

    print("=" * 80)
    print("开始编译 SatelliteCenter 包...")
    print(f"源目录：{src_package}")
    print(f"输出目录：{output_package}")
    print("=" * 80)

    # 首先复制 __init__.py 和 JSON 配置文件（不编译）
    print("\n📋 复制包配置文件...")
    for init_file in src_package.glob("**/__init__.py"):
        rel_path = init_file.relative_to(src_package)
        out_file = output_package / rel_path
        out_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(init_file, out_file)
        print(f"  ✓ {rel_path}")

    # 复制 JSON 文件
    for json_file in src_package.glob("**/*.json"):
        rel_path = json_file.relative_to(src_package)
        out_file = output_package / rel_path
        out_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(json_file, out_file)
        print(f"  ✓ {rel_path}")

    # 编译所有 .py 文件（除了 __init__.py）
    print("\n🔨 编译 Python 模块...")
    py_files = list(src_package.glob("**/*.py"))
    py_files = [f for f in py_files if f.name != "__init__.py"]

    if not py_files:
        print("  ⚠️  没有找到需要编译的 Python 文件")
        return

    print(f"  发现 {len(py_files)} 个模块，开始编译...")

    failed_files = []
    for py_file in py_files:
        rel_path = py_file.relative_to(src_package)
        print(f"\n  编译: {rel_path}")

        nuitka_args = [
            sys.executable,
            "-m",
            "nuitka",
            "--module",
            "--output-dir=" + str(output_package.parent),
            "--remove-output",
            "--quiet",
            str(py_file),
        ]

        try:
            subprocess.run(nuitka_args, check=True, capture_output=True)
            print(f"    ✅ 编译成功")

            # Nuitka 会在 output-dir 生成 .pyd/.so 文件，需要移到包目录
            # 查找生成的编译文件
            compiled_file = None
            for ext in [".pyd", ".so", ".pyc"]:
                candidate = output_package.parent / (py_file.stem + ext)
                if candidate.exists():
                    compiled_file = candidate
                    break

            if compiled_file and compiled_file.exists():
                dest = output_package / rel_path.parent / (py_file.stem + ".pyd")
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(compiled_file), str(dest))

        except subprocess.CalledProcessError as e:
            print(f"    ❌ 编译失败")
            failed_files.append(str(rel_path))

    print("\n" + "=" * 80)
    if failed_files:
        print(f"⚠️  编译完成，但 {len(failed_files)} 个文件失败：")
        for f in failed_files:
            print(f"  - {f}")
        print("\n这些文件的源代码仍然在输出目录中")
    else:
        print("✅ 所有文件编译成功！")

    print(f"\n📦 编译后的包位置：{output_package}")
    print("\n使用编译后的包：")
    print(f"1. 将 {output_package} 复制到你的部署环境")
    print("2. 确保依赖 (autowaterqualitymodeler, pandas, numpy) 已安装")
    print("3. 可以像使用正常的 Python 包一样导入使用")
    print("=" * 80)


if __name__ == "__main__":
    compile_package()
