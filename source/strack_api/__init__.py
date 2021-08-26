# coding=utf8
# Copyright (c) 2018 CineUse
import os
import sys

# Add vendor directory to module search path
parent_dir = os.path.abspath(os.path.dirname(__file__))
packages_dir = os.path.join(parent_dir, 'packages')

sys.path.append(packages_dir)
