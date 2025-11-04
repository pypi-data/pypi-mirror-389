import os
import sys
import subprocess
from pathlib import Path
import platform  # ✅ 新增：用于区分系统平台

TEMPLATE_URL = "https://github.com/778777266/npy_temp.git"


def run(cmd, cwd=None):
    """执行系统命令"""
    print(f"▶ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def show_help():
    """显示命令行帮助"""
    print(
        """
用法: npy <project_name>

示例:
  npy my_project

功能:
  从 Git 模板仓库 (https://github.com/778777266/npy_temp.git)
  自动创建新项目、生成虚拟环境并安装依赖。
"""
    )


def clone_template(project_name):
    """克隆模板项目"""
    print(f"🚀 正在从模板创建项目: {project_name}")
    run(f"git clone {TEMPLATE_URL} {project_name}")
    print("✅ 模板下载完成。")


def create_venv(project_dir):
    """创建虚拟环境"""
    print("⚙️ 正在创建虚拟环境 (.venv)...")
    run("python -m venv .venv", cwd=project_dir)
    print("✅ 虚拟环境已创建。")


def install_deps(project_dir):
    """安装依赖（自动判断系统平台 + 智能生成 requirements.txt）"""
    req = Path(project_dir) / "requirements.txt"

    # ✅ 若模板中没有 requirements.txt，则自动创建一个默认文件
    if not req.exists():
        print("⚠️ 未找到 requirements.txt，已自动生成默认依赖文件。")
        default_reqs = [
            "# 默认依赖，可按需修改",
            "requests>=2.31.0",
            "pandas>=2.2.0",
            "numpy>=1.26.0",
        ]
        req.write_text("\n".join(default_reqs), encoding="utf-8")

    print("📦 安装依赖...")

    # ✅ 根据系统自动识别 pip 路径
    if platform.system() == "Windows":
        pip_path = Path(project_dir) / ".venv" / "Scripts" / "pip.exe"
    else:
        pip_path = Path(project_dir) / ".venv" / "bin" / "pip"

    if not pip_path.exists():
        print("⚠️ 未找到 pip，请手动执行以下命令安装依赖：")
        print(f"   cd {project_dir}")
        if platform.system() == "Windows":
            print("   .venv\\Scripts\\activate")
        else:
            print("   source .venv/bin/activate")
        print("   pip install -r requirements.txt")
        return

    run(f'"{pip_path}" install -r requirements.txt', cwd=project_dir)
    print("✅ 依赖安装完成。")


def main():
    # ✅ 帮助命令
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        show_help()
        return

    project_name = sys.argv[1]
    project_dir = Path(project_name)

    # ✅ 避免覆盖已有目录
    if project_dir.exists():
        print(f"❗目录 {project_name} 已存在，请换个名字。")
        sys.exit(1)

    # Step 1: 拉取模板
    clone_template(project_name)

    # Step 2: 创建虚拟环境
    create_venv(project_dir)

    # Step 3: 安装依赖
    install_deps(project_dir)

    # Step 4: 完成提示
    print("\n🎉 项目创建完成！")
    print(f"➡️ cd {project_name}")
    print("➡️ 激活虚拟环境:")
    print("   Windows: .venv\\Scripts\\activate")
    print("   Linux/macOS: source .venv/bin/activate")
    print("➡️ 启动项目: python main.py\n")


if __name__ == "__main__":
    main()
