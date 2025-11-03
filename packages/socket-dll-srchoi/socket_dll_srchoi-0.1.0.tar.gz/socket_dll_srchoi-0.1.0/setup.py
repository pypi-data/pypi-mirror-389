"""
SocketDLL - Python 소켓 라이브러리 (C++ 기반)
"""

from setuptools import setup, find_packages
import os

# README 읽기
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="socket-dll-srchoi",
    version="0.1.0",
    author="srchoi",
    author_email="srchoi@example.com",
    description="고성능 C++ 소켓 라이브러리를 위한 Python 래퍼",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/srchoi/socket-dll",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
    ],
    python_requires=">=3.7",
    package_data={
        "socket_dll": ["bin/*.dll", "bin/*.so", "bin/*.dylib"],
    },
    include_package_data=True,
    keywords="socket tcp networking dll c++",
    project_urls={
        "Bug Reports": "https://github.com/srchoi/socket-dll/issues",
        "Source": "https://github.com/srchoi/socket-dll",
    },
)
