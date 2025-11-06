from setuptools import setup, find_packages
import codecs
import os


def read(fname):
    return codecs.open(os.path.join(os.path.dirname(__file__), fname)).read()


long_desc = """
PingAn API 
===============

pingan stock data api

"""


setup(
    name='dcube',
    version='1.0.2',
    description='stock data',

    # 程序的详细描述
    long_description=long_desc,
    url='https://datacube.foundersc.com/',
    keywords='Financial Data',

    # 程序的所属分类列表
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: BSD License'
    ],

    # 需要处理的包目录（包含__init__.py的文件夹）
    packages=['dcube', 'dcube/util', 'dcube/util/protobuf'],

    # 需要安装的依赖
    install_requires=[
        'requests>=2.0.0',
        'pandas>=0.16.0',
        'protobuf'
    ],
    include_package_data=True,
)
