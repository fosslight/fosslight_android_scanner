#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.help import PrintHelpMsg, print_package_version

_HELP_MESSAGE = """
    Usage: fosslight_android [option1] <arg1> [option2] <arg2>...

    List all the binaries loaded on the Android-based model to check which open source is used for each
    binary, and to check whether the notices are included in the OSS notice.
    (ex-NOTICE.html: OSS Notice for Android-based model).

    Options:
        Mandatory
            -s <android_source_path>\t   Path to analyze
            -a <build_log_file_name>\t   The file must be located in the android source path.

        Optional
            -h\t\t\t\t   Print help message
            -m\t\t\t\t   Analyze the source code for the path where the license could not be found.
            -e <path1> <path2..>\t   Path to exclude from source analysis.
            -p\t\t\t\t   Check files that should not be included in the Packaging file.
            -f\t\t\t\t   Print result of Find Command for binary that can not find Source Code Path.
            -i\t\t\t\t   Disable the function to automatically convert OSS names based on AOSP.
            -r <result.txt>\t\t   result.txt file with a list of binaries to remove."""


def print_help_msg():
    helpMsg = PrintHelpMsg(_HELP_MESSAGE)
    helpMsg.print_help_msg(True)


def print_version(pkg_name):
    print_package_version(pkg_name, "FOSSLight Android Version:")
