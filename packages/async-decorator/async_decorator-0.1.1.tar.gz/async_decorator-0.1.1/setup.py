from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="async-decorator",
    version="0.1.1",
    author="FadsII",
    author_email="594604366@qq.com",
    description="A flexible async/sync execution library with dedicated thread pools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/FadsII/async-decorator",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.15",
            "black>=21.0",
            "isort>=5.0",
            "mypy>=0.900",
            "twine>=4.0",
        ],
    },
    keywords="async, threading, executor, decorator",
)