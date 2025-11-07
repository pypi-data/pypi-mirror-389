from setuptools import setup, find_packages

setup(
    # 包名称（PyPI上的唯一标识）
    name="inference-python-sdk",
    # 版本号（遵循语义化版本：主版本.次版本.修订号）
    version="0.1.5",
    # Python版本要求
    python_requires=">=3.7",
    packages=find_packages(exclude=["deploy", "example"]),
    install_requires=[
            "httpx",
            "openai",
            "pyrate_limiter==2.7.0",
            "tenacity",
            "pyyaml"
        ],
    # 关键配置：递归包含所有YAML和Jinja2文件
    package_data={
        # 仅在已发现的包内递归包含模板/配置文件
        "synapse": [
            "**/*.yaml",
            "**/*.yml",
            "**/*.jinja2",
            "**/*.json",
        ],
    },
)
