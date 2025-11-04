from setuptools import setup, find_packages

setup(
    name="npyproj",             # ✅ 改这里（包名唯一）
    version="0.2.0",
    description="A lightweight Python project scaffolding CLI",
    author="778777266",
    author_email="workmail2000@qq.com",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "npy = npy.cli:main",  # ✅ 命令名保持 npy
        ],
    },
)
