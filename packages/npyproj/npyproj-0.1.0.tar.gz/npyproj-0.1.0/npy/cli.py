import os
import sys
import subprocess
from pathlib import Path

TEMPLATE_URL = "https://github.com/778777266/npy_temp.git"

def run(cmd, cwd=None):
    print(f"▶ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        sys.exit(result.returncode)

def show_help():
    print("""
用法: npy <project_name>

示例:
  npy my_project

功能:
  从 Git 模板仓库 (https://github.com/778777266/npy_temp.git)
  自动创建新项目、生成虚拟环境并安装依赖。
""")

def clone_template(project_name):
    print(f"🚀 正在从模板创建项目: {project_name}")
    run(f"git clone {TEMPLATE_URL} {project_name}")
    print("✅ 模板下载完成。")

def create_venv(project_dir):
    print("⚙️ 创建虚拟环境 (.venv)...")
    run("python -m venv .venv", cwd=project_dir)
    print("✅ 虚拟环境已创建。")

def install_deps(project_dir):
    req = Path(project_dir) / "requirements.txt"
    if req.exists():
        print("📦 安装依赖...")
        pip_path = Path(project_dir) / ".venv" / "Scripts" / "pip"
        if not pip_path.exists():
            pip_path = Path(project_dir) / ".venv" / "bin" / "pip"
        run(f"{pip_path} install -r requirements.txt", cwd=project_dir)
    else:
        print("⚠️ 未找到 requirements.txt，跳过依赖安装。")

def main():
    # ✅ 处理帮助参数
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        show_help()
        return

    project_name = sys.argv[1]
    project_dir = Path(project_name)

    if project_dir.exists():
        print(f"❗目录 {project_name} 已存在，请换个名字。")
        sys.exit(1)

    clone_template(project_name)
    create_venv(project_dir)
    install_deps(project_dir)

    print("\n🎉 项目创建完成！")
    print(f"➡️ cd {project_name}")
    print(f"➡️ 激活虚拟环境:")
    print("   Windows: .venv\\Scripts\\activate")
    print("   Linux/macOS: source .venv/bin/activate")
    print("➡️ 启动项目: python main.py\n")

if __name__ == "__main__":
    main()
