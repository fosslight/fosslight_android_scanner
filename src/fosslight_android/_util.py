#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging
import os
from datetime import datetime
from fosslight_util.constant import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def read_file(file_name_with_path, read_as_one_line=False):
    encodings = ["latin-1", "utf-8", "utf-16"]
    read_line = "" if read_as_one_line else []
    read_success = False
    for encoding_option in encodings:
        try:
            file = open(file_name_with_path, encoding=encoding_option)
            read_line = file.read() if read_as_one_line else file.readlines()
            file.close()
            if read_line is not None and len(read_line) > 0:
                read_success = True
                break
        except Exception:
            pass

    return read_success, read_line


def write_txt_file(file_name, str_to_write, run_command_dir):
    try:
        file_to_create = os.path.join(run_command_dir, file_name)
        f = open(file_to_create, 'w')
        f.write(str_to_write)
        f.close()
    except Exception as error:
        logger.info(f"Failed to write text:{file_to_create}\n{error}")


def get_path_by_using_find(file_list_to_find, build_out_path, result_file, run_command_dir):
    if file_list_to_find is None or len(file_list_to_find.keys()) == 0:
        return
    else:
        try:
            str_report = "BINARY\tFOUND_PATH\n"
            start_time = datetime.now()
            out_dir = build_out_path.split("/")[0]
            dirs_to_find = list(
                filter(lambda x: x != out_dir and not x.startswith("."), filter(os.path.isdir, os.listdir('.'))))
            for dir in dirs_to_find:
                for root, dirs, files in os.walk(dir):
                    for file in files:
                        if file in file_list_to_find:
                            file_list_to_find[file].append(os.path.join(root, file))

            for key, values in file_list_to_find.items():
                str_report += key + "\t\n\t" + "\n\t".join(values) + "\n"

            # Write file
            dt = datetime.now() - start_time
            s = dt.seconds
            ms = int(dt.microseconds / 1000)
            search_time = "* SEARCHING TIME: " + '{:02}:{:02}:{:02}.{:03}'.format(s // 3600, s % 3600 // 60, s % 60,
                                                                                  ms) + ", Number of binaries:" + str(
                len(file_list_to_find.keys()))
            str_report = search_time + "\r\n" + str_report
            write_txt_file(result_file, str_report, run_command_dir)
        except Exception as error:
            logger.error(f"FIND Command:{error}")
