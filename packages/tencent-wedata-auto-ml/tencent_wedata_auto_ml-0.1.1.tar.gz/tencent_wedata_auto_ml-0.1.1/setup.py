# -*- coding: utf-8 -*-
from pathlib import Path
from setuptools import setup, find_packages

BASE_DIR = Path(__file__).parent
README = (BASE_DIR / "README.md").read_text(encoding="utf-8") if (BASE_DIR / "README.md").exists() else ""

# Read version from package to avoid duplication
VERSION = None
init_py = BASE_DIR / "src" / "wedata_automl" / "__init__.py"
if init_py.exists():
    for line in init_py.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("__version__"):
            VERSION = line.split("=", 1)[1].strip().strip("'\"")
            break
if not VERSION:
    raise RuntimeError("Cannot find __version__ in src/wedata_automl/__init__.py")

setup(
    name="tencent-wedata-auto-ml",
    version=VERSION,
    description="AutoML SDK for Tencent Cloud WeData using FLAML with MLflow integration.",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Zhang Chun Lin",
    author_email="42547199+ZhangChunlin316@users.noreply.github.com",
    url="https://git.woa.com/WeDataOS/wedata-automl",
    project_urls={
        "Homepage": "https://git.woa.com/WeDataOS/wedata-automl",
        "Repository": "https://git.woa.com/WeDataOS/wedata-automl.git",
    },
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={"wedata_automl": ["templates/*.j2"]},
    install_requires=[
        "flaml",
        "mlflow",
        "scikit-learn",
        "pandas",
        "numpy",
        "tencent-wedata-feature-engineering==0.1.37",
    ],
    extras_require={
        "xgboost": ["xgboost"],
        "lightgbm": ["lightgbm"],
    },
    entry_points={
        "console_scripts": [
            "wedata-automl-demo=wedata_automl.cli:main",
        ]
    },
    keywords=["automl", "flaml", "mlflow", "wedata", "tencent"],
)

