#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Android binary analysis script
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import pytest


@pytest.fixture
def android_src_path():
    return os.getenv("ANDROID_SRC_PATH")


@pytest.fixture
def android_build_log():
    return os.getenv("ANDROID_BUILD_LOG")


@pytest.fixture
def run_command():
    def _run_command(command):
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        success = result.returncode == 0
        return success, result.stdout.decode('utf-8'), result.stderr.decode('utf-8')
    return _run_command