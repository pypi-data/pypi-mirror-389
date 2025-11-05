# -*- coding:UTF-8 -*-
import codecs
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

# 每个版本pypi只能使用1次
NAME = 'pyyutil'
VERSION = '0.0.1'
AUTHOR = 'yanyue'
DESCRIPTION = 'pyyutil是py高效工具'
LONG_DESCRIPTION = 'pyyutil是py高效工具'

setup(
    # name 唯一标识符 在pypi中搜索只有一个
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email="",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    install_requires=[],
    # 别人搜索的关键词
    keywords=['utils', 'python', 'pyyutil', 'python utils', 'windows', 'mac', 'linux'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        # 支持的系统
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)
