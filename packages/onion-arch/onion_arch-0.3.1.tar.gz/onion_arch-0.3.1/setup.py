#!/usr/bin/env python
# coding:utf-8
import os
from setuptools import setup, find_packages

setup(
    name='onion-arch',
    version='0.3.1',
    description="Decouple your package-project with Onion-Mode.",
    long_description=open(r'T:\New_PC\Import_Project\uploads\onion_upload\readme.en.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author_email='2229066748@qq.com',
    maintainer="Eagle'sBaby",
    maintainer_email='2229066748@qq.com',
    packages=["oarch"],
    # package_data={
    #     '': ['*.7z'],
    # },
    license='Apache Licence 2.0',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    # entry_points={
    #     'console_scripts': [
    #         'pyscreeps-arena=pyscreeps_arena:CMD_NewProject',
    #     ]
    # },
    keywords=['python'],
    python_requires='>=3.10',
    # install_requires=[
    #     'pyperclip',
    #     'colorama',
    #     'py7zr',
    #     'Transcrypt==3.9.1',
    #     'mkdocs',
    #     'mkdocstrings[python]',
    #     'mkdocs-material',
    # ],
)
