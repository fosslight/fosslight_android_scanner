#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Android binary analysis script
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import pytest

import os


def test_fosslight_android(run_command, android_src_path, android_build_log):

    # given
    assert android_src_path, "android_src_path is not set."
    assert android_build_log, "android_build_log is not set."

    # when
    command = f"fosslight_android -s {android_src_path} -a {android_build_log} -m"
    success, _, stderr = run_command(command)

    # then
    assert success is True, f"fosslight_android test_run failed. stderr: {stderr}"


def test_release_environment(run_command):

    # given
    run_command("rm -rf test_result")
    os.makedirs("test_result", exist_ok=True)

    # when
    help_result, _, _  = run_command("fosslight_android -h")
    ok_result, _, _ = run_command("fosslight_android -b test/binary.txt -n test/NOTICE.html -c ok")
    nok_result, _, _  = run_command("fosslight_android -b test/binary.txt -n test/NOTICE.html -c nok")
    divide_result, _, _ = run_command("fosslight_android -d test/needtoadd-notice.html")

    # then
    assert help_result is True, "Help command failed"
    assert ok_result is True, "OK command failed"
    assert nok_result is True, "NOK command failed"
    assert divide_result is True, "Divide command failed"
