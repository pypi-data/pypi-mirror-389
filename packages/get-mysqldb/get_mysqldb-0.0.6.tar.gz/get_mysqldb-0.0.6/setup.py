#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

setup(
    name='get_mysqldb',  # 项目的名称,pip3 install get-time
    version='0.0.6',  # 项目版本
    author='MindLullaby',  # 项目作者
    author_email='3203939025@qq.com',  # 作者email
    # url='',  # 项目代码仓库
    description='mysql数据存储',  # 项目描述
    packages=['get_mysqldb'],  # 包名
    install_requires=[
        "pymysql",
        "loguru",
        "dbutils==3.1.0"
    ],
)
