#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Version 1.0
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import shutil


def copy_and_create_dir(input_dir):
    cwd = os.getcwd()

    notice_dir = os.path.join(cwd, "additional_notice_files")
    dest_folder = os.path.join(cwd, input_dir)
    if not os.path.isdir(dest_folder):
        os.makedirs(dest_folder)

    if os.path.isdir(notice_dir):
        for root, dirs, files in os.walk(notice_dir):
            for file in files:
                if file.endswith(".txt"):
                    try:
                        src_file = os.path.join(root, file)
                        relative_path = os.path.relpath(root, notice_dir)
                        dist_path = os.path.join(dest_folder, relative_path)
                        if not os.path.isdir(dist_path):
                            os.makedirs(dist_path)
                        if not os.path.exists(os.path.join(dist_path, file)):
                            shutil.copy2(src_file, dist_path)

                    except Exception:
                        pass
