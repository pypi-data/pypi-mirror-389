#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="koxs_terminal_tools",
    version="0.2.9",
    author="koxs",
    author_email="2931205209@qq.com",  # 请替换为你的邮箱
    description="一个功能强大的终端工具集合",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=[
        # 如果有依赖包，在这里添加
        # "requests>=2.25.1",
        # "colorama>=0.4.4",
    ],
    entry_points={
        "console_scripts": [
            # 如果有命令行工具，在这里添加
            # "koxs-tools=koxs_terminal_tools.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "terminal",
        "tools", 
        "file operations",
        "color output",
        "encoding",
        "koxs",
    ],
    project_urls={
        "Bug Reports": "https://github.com/koxs/koxs_terminal_tools/issues",
        "Source": "https://github.com/koxs/koxs_terminal_tools",
        "Documentation": "https://github.com/koxs/koxs_terminal_tools/wiki",
    },
)