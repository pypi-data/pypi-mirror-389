from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tgmrkt-api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["requests>=2.28.0"],
    python_requires=">=3.7",
    author="Nsvl",
    description="Python wrapper for TG MRKT API - Telegram marketplace for gifts and stickers trading",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
    ],
    keywords="telegram tgmrkt nft gifts stickers marketplace trading api",
)