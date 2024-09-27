#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Android binary analysis script
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import pytest

def test_fosslight_android(run_command, android_src_path, android_build_log):

    # given
    assert android_src_path, "android_src_path is not set."
    assert android_build_log, "android_build_log is not set."

    # when
    command = f"fosslight_android -s {android_src_path} -a {android_build_log} -m"
    success, stdout, stderr = run_command(command)

    # then
    assert success is True, f"fosslight_android test_run failed. stderr: {stderr}"