#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Android binary analysis script
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0


import os
import pytest


@pytest.mark.run
def test_fosslight_android(run_command, android_src_path, android_build_log):

    # given
    assert android_src_path, "android_src_path is not set."
    assert android_build_log, "android_build_log is not set."

    # when
    command = f"fosslight_android -s {android_src_path} -a {android_build_log} -m"
    success, stdout, stderr = run_command(command)

    # then
    assert success is True, f"fosslight_android test_run failed. stderr: {stderr}"


@pytest.mark.release
def test_release_environment(run_command):

    # given
    test_result, _, _ = run_command("rm -rf test_result")
    os.makedirs("test_result", exist_ok=True)

    # when
    help_result, _, _ = run_command("fosslight_android -h")
    success, _, _ = run_command("fosslight_android -s test/android_12_sample -a android.log")

    # then
    assert help_result is True, "Help command failed"
    assert success is True, "Test was failed"
