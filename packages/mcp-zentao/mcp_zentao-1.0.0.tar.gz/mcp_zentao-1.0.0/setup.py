#!/usr/bin/env python3
"""
Setup script for mcp-zentao package
"""
from setuptools import setup, find_packages

setup(
    name="mcp-zentao",
    version="1.0.0",
    description="禅道系统 MCP 服务器 - 基于 Semantic Kernel 的 Model Context Protocol 服务器",
    author="nblog",
    author_email="your-email@example.com",
    url="https://github.com/wrcopilot-org/mcp-zentao",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "httpx>=0.28.1",
        "pydantic>=2.11.7",
        "pydantic-settings>=2.10.1",
        "semantic-kernel[mcp]>=1.32.2",
    ],
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "mcp-zentao=mcp_zentao.sk_mcp_server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords=["mcp", "zentao", "semantic-kernel", "ai", "project-management"],
    project_urls={
        "Homepage": "https://github.com/wrcopilot-org/mcp-zentao",
        "Repository": "https://github.com/wrcopilot-org/mcp-zentao",
        "Documentation": "https://github.com/wrcopilot-org/mcp-zentao#readme",
        "Bug Tracker": "https://github.com/wrcopilot-org/mcp-zentao/issues",
    },
)