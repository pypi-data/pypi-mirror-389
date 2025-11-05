from setuptools import setup, find_packages
from pathlib import Path

# README 파일 읽기
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="vector-matrix-overloading",
    version="0.1.0",
    author="Dongbin Shin",
    author_email="dongbin369085@gmail.com",
    description="벡터와 행렬 연산을 위한 연산자 오버로딩 패키지",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/vector-matrix-overloading",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Mathematics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    keywords="vector matrix linear-algebra operator-overloading mathematics",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/vector-matrix-overloading/issues",
        "Source": "https://github.com/yourusername/vector-matrix-overloading",
    },
)

