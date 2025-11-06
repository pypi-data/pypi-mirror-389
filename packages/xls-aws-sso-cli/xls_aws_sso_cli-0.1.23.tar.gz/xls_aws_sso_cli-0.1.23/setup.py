from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="xls-aws-sso-cli",
    version="0.1.23",
    author="Fahrizal Shofyan Aziz",
    author_email="fahrizalshofyanaziz@gmail.com",
    description="AWS SSO Management CLI Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fahrizalvianaz/python-cli",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.7.0",
        "inquirerpy>=0.3.4",
    ],
    entry_points={
        "console_scripts": [
            "xls-sso=xls_aws_sso_cli:main",
        ],
    },
)