from setuptools import setup, find_packages

setup(
    name="ctyun-cli",
    version="0.1.0a1",
    description="天翼云CLI工具 - 基于终端的云资源管理平台",
    author="Your Name",
    author_email="your.email@example.com",
    packages=["ctyun_cli"] + ["ctyun_cli." + p for p in find_packages(where="src")],
    package_dir={"ctyun_cli": "src"},
    install_requires=[
        "requests>=2.31.0",
        "click>=8.1.0",
        "cryptography>=41.0.0",
        "colorama>=0.4.6",
        "tabulate>=0.9.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ctyun-cli=ctyun_cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)