#!/usr/bin/python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='oakbay-py-client',
    version='0.1.0',
    packages=['.', 'oakbayThrift', 'oakbayThrift.LindenCommon', 'oakbayThrift.OakbayClient'],
    package_dir={'': 'src/main/python'},
    url='',
    license='',
    author='lab',
    author_email='zhaoyonghui@xiaomi.com',
    description=''
)
