#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from codecs import open
from setuptools import setup, find_packages


with open('README.md', 'r', 'utf-8') as f:
    readme = f.read()


with open('requirements.txt', 'r', 'utf-8') as f:
    required = f.read().splitlines()


if __name__ == "__main__":
    setup(
        name='fosslight_android',
        version='5.0.9',
        package_dir={"": "src"},
        packages=find_packages(where='src'),
        description='FOSSLight Android Scanner',
        long_description=readme,
        long_description_content_type='text/markdown',
        license='Apache-2.0',
        author='LG Electronics',
        url='https://github.com/fosslight/fosslight_android_scanner',
        download_url='https://github.com/fosslight/fosslight_android_scanner',
        classifiers=['License :: OSI Approved :: Apache Software License',
                     "Programming Language :: Python :: 3",
                     "Programming Language :: Python :: 3.10",
                     "Programming Language :: Python :: 3.11",
                     "Programming Language :: Python :: 3.12"],
        python_requires='>=3.10, <3.13',
        install_requires=required,
        include_package_data=True,
        entry_points={
            "console_scripts": [
                "fosslight_android = fosslight_android.android_binary_analysis:main"
            ]
        }
    )
