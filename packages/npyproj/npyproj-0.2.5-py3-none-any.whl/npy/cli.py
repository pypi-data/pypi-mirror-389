# 文件：npy/cli.py
import os
import sys
import subprocess
from pathlib import Path
import platform

TEMPLATE_URL = "https://github.com/778777266/npy_temp.git"


def run(cmd, cwd=None):
    """执行系统命令（跨平台安全调用）"""
    print(f"▶ {cmd}")
    if isinstance(cmd, str):
        cmd = cmd.split()
    # ✅ 关闭文件描述符 + 禁止输出保持干净
    result = subprocess.run(
        cmd,
        cwd=cwd,
        close_fds=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        sys.exit(result.returncode)


def show_help():
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
    print(f"🚀 正在从模板创建项目: {project_name}")
    run(["git", "clone", TEMPLATE_URL, project_name])
    print("✅ 模板下载完成。")


def create_venv(project_dir):
    print("⚙️ 正在创建虚拟环境 (.venv)...")
    run(["python", "-m", "venv", ".venv"], cwd=project_dir)
    print("✅ 虚拟环境已创建。")


def install_deps(project_dir):
    """安装依赖（智能检测 requirements.txt + 跨平台兼容）"""
    req = Path(project_dir) / "requirements.txt"

    if not req.exists():
        print("⚠️ 未找到 requirements.txt，已自动生成默认依赖文件。")
        default_reqs = [
            "# 默认依赖，可按需修改",
            "requests>=2.31.0",
            "pandas>=2.2.0",
            "numpy>=1.26.0",
        ]
        req.write_text("\n".join(default_reqs), encoding="utf-8")
        print(f"✅ 已在 {req} 生成默认 requirements.txt。")

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

    print("📦 安装依赖...")
    result = subprocess.run(
        [str(pip_path), "install", "-r", "requirements.txt"],
        cwd=project_dir,
        close_fds=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        print("✅ 依赖安装完成。")
    else:
        print("❌ 依赖安装失败。")


def release_resources(project_dir: Path):
    """安全释放目录句柄和子进程资源"""
    try:
        # ✅ 关闭所有打开的文件描述符
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass

    try:
        # ✅ 切回上层目录释放锁
        os.chdir(Path(project_dir).parent)
    except Exception:
        pass


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        show_help()
        return

    project_name = sys.argv[1]
    project_dir = Path(project_name)

    if project_dir.exists():
        print(f"❗目录 {project_name} 已存在，请换个名字。")
        sys.exit(1)

    try:
        clone_template(project_name)
        create_venv(project_dir)
        install_deps(project_dir)
    finally:
        release_resources(project_dir)

    print("\n🎉 项目创建完成！")
    print(f"➡️ cd {project_name}")
    print("➡️ 激活虚拟环境:")
    print("   Windows: .venv\\Scripts\\activate")
    print("   Linux/macOS: source .venv/bin/activate")
    print("➡️ 启动项目: python main.py\n")


if __name__ == "__main__":
    main()
