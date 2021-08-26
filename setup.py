# coding=utf8
# Copyright (c) 2018 CineUse
import os
import re

from setuptools import setup, find_packages

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.md')

# Read version from source.
with open(
        os.path.join(SOURCE_PATH, 'strack_api', '_version.py')
) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)

# Call main setup.
setup(
    name='strack3-python-api',
    version=VERSION,
    description='Python API for Strack.',
    long_description=open(README_PATH).read(),
    keywords='strack, python, api',
    url='http://www.cineuse.com/',
    author='cineuse',
    author_email='support@cineuse.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={
        '': 'source'
    },

    install_requires=[
        # 'requests >= 2, <3', 'six'
    ],
    zip_safe=False
)
