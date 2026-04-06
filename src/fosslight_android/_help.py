#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.help import PrintHelpMsg, print_package_version

_HELP_MESSAGE_ANDROID = """
    📖 Usage
    ────────────────────────────────────────────────────────────────────
    fosslight_android [options] <arguments>

    📝 Description
    ────────────────────────────────────────────────────────────────────
    FOSSLight Android Scanner lists all the binaries loaded on the
    Android-based model to check which open source is used for each
    binary, and to check whether the notices are included in the OSS
    notice (ex. NOTICE.html: OSS Notice for Android-based model).

    📚 Guide: https://fosslight.org/fosslight-guide-en/android

    ⚙️  General Options
    ────────────────────────────────────────────────────────────────────
    -h                     Show this help message
    -v                     Show version information

    🔍 Scanner-Specific Options
    ────────────────────────────────────────────────────────────────────
    -s <path>              Path to the Android source (default: current directory)
    -a <build_log_file>    Build log file name (the file must be located in the
                           Android source path)
    -m                     Analyze source code for paths where the license
                           could not be found
    -e <path1> <path2>     Paths to exclude from source analysis
                           ⚠️  IMPORTANT: Always wrap in quotes to avoid shell expansion
                           Example: fosslight_android -e "test/" "vendor/sample/"
    -p <path>              Check files that should not be included in the
                           packaging file (uses pkgConfig.json for filtering rules)
    -f                     Print result of find command for binaries that cannot
                           find a source code path
    -i                     Disable automatic OSS name conversion based on AOSP
    -r <result.txt>        result.txt file with a list of binaries to remove

    💡 Examples
    ────────────────────────────────────────────────────────────────────
    # Scan current directory with build log
    fosslight_android -s /path/to/android -a android_build.log

    # Scan with source analysis for unlicensed binaries
    fosslight_android -s /path/to/android -a build.log -m

    # Scan with exclusions
    fosslight_android -s /path/to/android -a build.log -e "test/" "vendor/sample/"

    # Check packaging files
    fosslight_android -p /path/to/packaging/root
"""


def print_help_msg():
    helpMsg = PrintHelpMsg(_HELP_MESSAGE_ANDROID)
    helpMsg.print_help_msg(True)


def print_version(pkg_name):
    print_package_version(pkg_name, "FOSSLight Android Version:")
