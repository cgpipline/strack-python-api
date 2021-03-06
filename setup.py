# coding=utf8

import os
import re

from setuptools import setup, find_packages

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'src')
README_PATH = os.path.join(ROOT_PATH, 'README.md')

requires = [
    'chardet >= 4.0',
    'requests >= 2, <3',
    'six >=1.16,<2'
]

# Read version from src.
with open(
        os.path.join(SOURCE_PATH, 'strack_api', '_version.py'), 'r', encoding='UTF-8'
) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)

# Call main setup.
setup(
    name='strack-api',
    version=VERSION,
    description='Python API for Strack.',
    long_description=open(README_PATH, 'r', encoding='UTF-8').read(),
    keywords='strack, python, api',
    url='https://github.com/cgpipline/strack',
    author='strack',
    author_email='weiwei163@foxmail.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={
        '': 'src'
    },

    install_requires=requires,
    zip_safe=False
)
