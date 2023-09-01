#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

# Checking packaging files
import fnmatch
import tarfile
import zipfile
import os
import logging
import json
import sys
import contextlib
from datetime import datetime
from ._util import read_file
from fosslight_util.constant import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

# Filtering list
pkg_name_filter = []
pkg_extension_filter = []
pkg_path_filter = []
# Filtered list
prohibited_file_names = []
prohibited_file_extensions = []
prohibited_path_list = []
failed_to_read_path = []


def check_packaging_files(root_path):
    read_packaging_config()
    check_pkg_files_recursively(root_path)

    # Print result
    logger.warn("1. Prohibited file names :" + str(len(prohibited_file_names)))
    logger.warn('\n'.join(map(str, prohibited_file_names)))
    logger.warn("2. Prohibited file extension :" + str(len(prohibited_file_extensions)))
    logger.warn('\n'.join(map(str, prohibited_file_extensions)))
    logger.warn("3. Prohibited Path :" + str(len(prohibited_path_list)))
    logger.warn('\n'.join(map(str, prohibited_path_list)))
    logger.warn("4. Fail to read :" + str(len(failed_to_read_path)))
    logger.warn('\n'.join(map(str, failed_to_read_path)))


def read_packaging_config():
    global pkg_name_filter, pkg_extension_filter, pkg_path_filter
    config_file = "pkgConfig.json"

    read_success, config_content = read_file(config_file, True)

    if not read_success:
        logger.error("Enter a config file name with path:")
        config_file = input()
        read_success, config_content = read_file(config_file, True)
    if not read_success or config_content == "":
        logger.error("Fail to read config file for checking packaging files")
        sys.exit(1)

    # Read value from config json.
    config_json_obj = json.loads(config_content)
    pkg_name_filter = config_json_obj["Prohibited_File_Names"]
    pkg_extension_filter = config_json_obj["Prohibited_File_Extensions"]
    pkg_path_filter = config_json_obj["Prohibited_Path"]


def check_pkg_files_recursively(path):
    global prohibited_file_names, prohibited_file_extensions, prohibited_path_list, failed_to_read_path
    path_to_check = path
    result = True

    if os.path.isfile(path):
        result, path_to_check = extract_file(path)
    if not result or path_to_check == "":
        failed_to_read_path.append(path)
        return

    try:
        for root, directories, filenames in os.walk(path_to_check):
            # Find prohibited file name
            for name_to_find in pkg_name_filter:
                for filename in fnmatch.filter(filenames, "*" + name_to_find + "*"):
                    prohibited_file_names.append(os.path.join(root, filename))
            # Find prohibited file extension
            for extension in pkg_extension_filter:
                for filename in fnmatch.filter(filenames, "*." + extension):
                    prohibited_file_extensions.append(os.path.join(root, filename))
            # Find prohibited path
            path_for_dirs = []
            for dir in directories:
                path_for_dirs.append(os.path.join(root, dir))
            for path in pkg_path_filter:
                for path_item in fnmatch.filter(path_for_dirs, "*" + path + "*"):
                    prohibited_path_list.append(path_item)
            # Extract files
            for filename in fnmatch.filter(filenames, '*.tar.gz'):
                check_pkg_files_recursively(os.path.join(root, filename))
            for filename in fnmatch.filter(filenames, '*.tar'):
                check_pkg_files_recursively(os.path.join(root, filename))
            for filename in fnmatch.filter(filenames, '*.zip'):
                check_pkg_files_recursively(os.path.join(root, filename))

    except Exception:
        failed_to_read_path.append(path)


def unzip(source_file, dest_path):
    try:
        fzip = zipfile.ZipFile(source_file, 'r')
        for filename in fzip.namelist():
            fzip.extract(filename, dest_path)
        fzip.close()
    except Exception:
        return False, ""
    return True, dest_path


def extract_file(fname):
    extract_path = os.path.join(os.path.dirname(fname),
                                os.path.basename(fname) + "_extracted_by_script_" + datetime.today().strftime('%Y%m%d'))
    try:
        if not os.path.exists(extract_path):
            os.makedirs(extract_path)  # Create a directory to extract.
        else:  # The directory to extract already exists.
            return False, ""

        # Unzip the file.
        if fname.endswith(".tar.gz"):
            with contextlib.closing(tarfile.open(fname, "r:gz")) as t:
                t.extractall(path=extract_path)
        elif fname.endswith(".tar"):
            with contextlib.closing(tarfile.open(fname, "r:")) as t:
                t.extractall(path=extract_path)
        elif fname.endswith(".zip"):
            return unzip(fname, extract_path)
        else:
            return False, ""
    except Exception:  # When error occurs.
        return False, ""
    return True, extract_path
