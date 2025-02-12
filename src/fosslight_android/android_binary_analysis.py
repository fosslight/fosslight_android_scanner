#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Android binary analysis script
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import sys
from datetime import datetime
import os
import re
import json
import logging
# Parsing NOTICE
from bs4 import BeautifulSoup
import subprocess
# For tlsh comparison
import tlsh
import hashlib
# For checking repository name
import urllib.request
import multiprocessing
import parmap
import numpy as np
from functools import partial
from fosslight_util.set_log import init_log
from ._util import (
    read_file,
    write_txt_file,
    get_path_by_using_find
)
from .check_package_file import check_packaging_files
from .check_notice_file import (
    run_notice_html_checklist,
    find_bin_in_notice,
    read_notice_file,
    create_additional_notice,
    divide_notice_files_by_binary
)
from ._binary_db_controller import get_oss_info_from_db
from ._common import (
    AndroidBinary,
    CONST_NULL,
    CONST_TLSH_NULL,
    MODULE_INFO_FILE_NAME,
    MODULE_TYPE_NAME,
    skip_license,
    NOTICE_FILE_NAME,
    PKG_NAME
)
import yaml
from ._help import print_help_msg, print_version
from fosslight_util.constant import LOGGER_NAME
from fosslight_binary.binary_analysis import return_bin_only
import argparse
from pathlib import Path
from fosslight_util.oss_item import ScannerItem
from fosslight_util.output_format import write_output_file

EXCEPTIONAL_PATH = [r"(/)+gen/META/lic_intermediates/"]
android_log_lines = []
python_script_dir = ""

logger = logging.getLogger(LOGGER_NAME)

final_bin_info = []
module_info_json_obj = {}
build_out_path = ""  # ex -out/target/product/generic/
build_out_notice_file_path = ""  # build out/target/product/generic/obj/NOTICE.html
notice_file_list = {}  # Save file list in NOTICE.html
platform_version = ""  # Android Version. ex- 7.0.0.r1 -> 7.0

# Define Const Variables
NOTICE_HTML_FILE_NAME = ""
ANDROID_LOG_FILE_NAME = "android.log"
num_cores = 1
now = ""
HIDDEN_HEADER = {'TLSH', "SHA1"}
HEADER = {'BIN (Android)': ['ID', 'Binary Path', 'Source Path', 'Notice', 'OSS Name',
                            'OSS Version', 'License', 'Download Location', 'Homepage',
                            'Copyright Text', 'License Text', 'Exclude', 'Comment',
                            'Need Check', 'TLSH', 'SHA1']}

# For checking repository's name
repositories = {}

# For checking MODULE_LICENSE* files
_BASE_DIR = os.path.dirname(__file__)
_RESOURCES_DIR = os.path.join(_BASE_DIR, "resources")
_MODULE_LICENSE = os.path.join(_RESOURCES_DIR, "module_license.json")
_TAG_FILE_TABLE = {}
meta_lic_files = {}


def do_multi_process(func, input_list):
    manager = multiprocessing.Manager()
    return_list = manager.list()
    splited_data = np.array_split(input_list, num_cores)
    splited_data = [x.tolist() for x in splited_data]

    parmap.map(func, splited_data, return_list, pm_pbar=True,
               pm_processes=num_cores)

    return return_list


def get_oss_component_name(directory, default_name, default_version):
    final_oss_name = default_name
    oss_version = default_version
    repo_link = ""
    try:
        # Set oss component name as path
        directories = directory.split('/')
        for idx in range(len(directories), 0, -1):
            found_repository = "/".join(directories[0:idx])
            if found_repository in repositories:
                final_oss_name = "android-" + found_repository.replace('/', '-')
                oss_version = platform_version
                repo_link = repositories.get(found_repository, "")
                break
    except Exception as error:
        logger.debug(f"get_oss_component:{error}")

    return final_oss_name, oss_version, repo_link


def find_bin_license_info():
    global final_bin_info, _TAG_FILE_TABLE

    try:
        with open(_MODULE_LICENSE) as json_file:
            _TAG_FILE_TABLE = json.load(json_file)
        find_meta_lic_files()
    except Exception as error:
        logger.error(f"find_bin_license:{error}")

    return_list = do_multi_process(find_tag_file, final_bin_info)
    final_bin_info = return_list[:]


def get_module_json_obj_by_installed_path(module_name, binary_name_with_path, binary_name_only):
    global module_info_json_obj

    if module_name == "" or binary_name_with_path == "":
        return ""

    js_value = ""

    if module_name in module_info_json_obj:  # Binary Name without extension
        js_value = module_info_json_obj[module_name]
        js_value[MODULE_TYPE_NAME] = module_name
        return js_value
    elif binary_name_only in module_info_json_obj:  # Binary Name
        js_value = module_info_json_obj[binary_name_only]
        js_value[MODULE_TYPE_NAME] = binary_name_only
        return js_value
    else:  # Find binary by installed path
        for key in module_info_json_obj:
            js_value = module_info_json_obj[key]
            output_files = js_value.get("installed",None)
            if output_files is not None:
                for output_file in output_files:
                    if output_file == binary_name_with_path:
                        js_value[MODULE_TYPE_NAME] = key
                        return js_value
                    else:
                        path_with_out_dir = os.path.join(build_out_path, binary_name_with_path)
                        if path_with_out_dir == output_file:
                            js_value[MODULE_TYPE_NAME] = key
                            return js_value
            
    return ""


def read_module_info_from_build_output_file():
    global module_info_json_obj

    # Only in case upper 7.0.0 versions have a module-info.mk at build/core/tasks.
    # Lower versions sould copy module-info.mk to build/core/tasks than build it again.
    if not os.path.isfile(os.path.join(build_out_path, MODULE_INFO_FILE_NAME)):
        logger.warn("BUILD OUTPUT PATH :", build_out_path)
        logger.warn("Can't find a module-info.json file at build output path.")
        logger.warn("Please copy module-info.mk file to build/core/tasks than build it again.")
        sys.exit(1)

    try:
        module_f = os.path.join(build_out_path, MODULE_INFO_FILE_NAME)
        f = open(module_f, 'r')
        module_info_json_obj = json.loads(f.read())
        f.close()

    except IOError:
        logger.warn("[ERROR] Cannot read ", MODULE_INFO_FILE_NAME)


def set_env_variables_from_result_log():
    global build_out_path, build_out_notice_file_path, platform_version

    # Check the platform version
    for line in android_log_lines:
        try:
            line = line.strip()
            pattern = re.compile(r'.*PLATFORM_VERSION\s*=\s*(\d+.?\d?)(.*\d*)\S*\s*')
            matched = pattern.match(line)
            if matched is not None:
                platform_version = matched.group(1)
                break

        except Exception:
            pass

    # FIND a NOTICE file and build out path
    for line in reversed(android_log_lines):
        line = line.strip()
        if line.endswith("obj/NOTICE.xml") or line.endswith("obj/NOTICE.html") or line.endswith("obj/NOTICE.txt"):
            words = line.split()
            build_out_notice_file_path = words[-1]
            find_idx = build_out_notice_file_path.find("obj/")
            build_out_path = build_out_notice_file_path[:find_idx]
            break

    if build_out_path == "":
        for line in reversed(android_log_lines):
            try:
                pattern = re.compile(r'.*Installed file list\s*(.*):\s*(.*)')
                matched = pattern.match(line)
                if matched is not None:
                    build_out_path = os.path.dirname(matched.group(2))
                    break
            except Exception:
                pass
        if build_out_path == "":
            logger.error("Can't find a build output path.")
            sys.exit(1)

    if build_out_notice_file_path == "":
        build_out_notice_file_path = os.path.join(build_out_path, "obj")

    read_module_info_from_build_output_file()


def find_binaries_from_out_dir():
    global build_out_path

    if build_out_path.endswith("/"):
        build_out_path = build_out_path[:-1]
        build_out_path = build_out_path.strip()

    system_path = os.path.join(build_out_path, "system")
    root_path = os.path.join(build_out_path, "root")
    obj_static_lib = os.path.join(build_out_path, "obj/STATIC_LIBRARIES")
    font_path = os.path.join(build_out_path, "system/fonts")
    cmd_list = [
        "find " + system_path + " -type f -exec file \"{}\" \\; | "
        "egrep \"ELF\\ |ARM,|\\.jar|\\.apk\" | grep -v \"\\.o:\" | "
        "grep -v \"\\.odex:\" | awk -F\":\" \'{print $1}\'",
        "find " + root_path + " -type f -exec file \"{}\" \\; | "
        "egrep \"ELF\\ |ARM,|\\.jar|\\.apk\" | grep -v \"\\.o:\" | awk -F\":\" \'{print $1}\' ",
        "find " + build_out_path + " -maxdepth 1 -type f -exec file \"{}\" \\; | grep data$ |"
        " grep -v .img  | awk -F\":\" \'{print $1}\' ",
        "find " + obj_static_lib + " -type f -exec file \"{}\" \\; | egrep \"ar archive\" | awk -F\":\" \'{print $1}\' ",
        f"find {build_out_path} ! \\( \\( -type d -path {system_path}"
        f" -o -path {root_path} -o -path \'{build_out_path}"
        f"/obj*\' -o -path {build_out_path}/symbols -o -path \'"
        f"{build_out_path}/factory_*\' -o -path {build_out_path}"
        "/dex_bootjars \\) -prune \\)  -type f -exec file \"{}\" \\; | egrep \"ELF\\ |ARM,|\\.jar|\\.apk\" | "
        "grep -v \"\\.o:\" | grep -v \"\\.odex:\" | awk -F\":\" \'{print $1}\' ",
        "find " + font_path + " -type f -exec file \"{}\" \\; | egrep \"font\" | awk -F\":\" \'{print $1}\'"
    ]

    return_list = do_multi_process(find_binary, cmd_list)
    tmp_files = []
    for file_rel_path in return_list:
        if any(re.search(re_except_path, file_rel_path) for re_except_path in EXCEPTIONAL_PATH):
            #logger.debug(f"REMOVE (Exceptional Path):{file_rel_path}")
            continue
        else:
            bin_item = AndroidBinary(os.path.abspath(file_rel_path))
            bin_item.binary_name_without_path = os.path.basename(file_rel_path)
            bin_item.bin_name_with_installed_path = file_rel_path
            tmp_files.append(bin_item)

    tmp_bin_files = list(return_bin_only(tmp_files, False))
    return_list = [x.bin_name_with_installed_path for x in tmp_bin_files]
    return return_list


def find_binary(cmd_list, install_list):
    for cmd in cmd_list:
        result = str(subprocess.check_output(cmd, shell=True, universal_newlines=True)).replace('\n', " ")
        if result is not None:
            result = result.split()
            install_list.extend(result)


def find_license_from_meta(module_name, bin_name):
    lic = ""
    key = module_name
    if module_name not in meta_lic_files:
        key = Path(bin_name).stem
    if key in meta_lic_files:
        lic = meta_lic_files.get(key, "")
    return lic


def find_tag_file(bin_info_list, return_bin_list):
    for item in bin_info_list:
        dir_path = item.source_code_path
        item.license = CONST_NULL
        try:
            module_license_files = [x for x in os.listdir(dir_path) if x.startswith('MODULE_LICENSE_')]
            if module_license_files is not None and len(module_license_files) > 0:
                for module_license_file in module_license_files:
                    item.license = module_license_file.replace('MODULE_LICENSE_', '')
                    if item.license in _TAG_FILE_TABLE:
                        item.license = _TAG_FILE_TABLE[item.license]
        except Exception:
            item.license = CONST_NULL
        if item.license == CONST_NULL:
            item.license = find_license_from_meta(item.module_name, item.binary_name_without_path)
    return_bin_list.extend(bin_info_list)


def get_result_of_notice_html(found_on_html, notice_file_found):
    if found_on_html and notice_file_found:
        return "ok"
    elif found_on_html and not notice_file_found:
        return "ok(NA)"
    elif notice_file_found and not found_on_html:
        return "nok(NA)"
    else:
        return "nok"


def find_notice_value():
    global notice_file_list, final_bin_info
    str_notice_files = ""

    try:
        notice_file_list, notice_files = read_notice_file(os.path.abspath(build_out_notice_file_path), NOTICE_HTML_FILE_NAME)
        if not notice_file_list:
            logger.info(f"Notice file is empty:{notice_files}")
            return
        if notice_files:
            for notice_file in notice_files:
                if "NOTICE.txt" in notice_file:
                    logger.debug(f"NOTICE.txt: {notice_file}")
                    notice_files.remove(notice_file)
            str_notice_files = ",".join(notice_files)
            logger.info(f"Notice files:{str_notice_files}")
        else:
            logger.debug("Can't find a notice file")
        return_list = do_multi_process(find_notice_html, final_bin_info)
        final_bin_info = return_list[:]

    except IOError as error:  # 'CANNOT_FIND_NOTICE_HTML'
        logger.debug(f"find_notice_value:{error}")
    return str_notice_files


def find_notice_html(bin_info, return_list):
    for item in bin_info:
        output = ""
        try:
            output = item.bin_name
            check_notice_html = find_bin_in_notice(output, notice_file_list)
            check_notice_file_exist_at_path = os.path.isfile(
                os.path.join(item.source_code_path, NOTICE_FILE_NAME))
            item.notice = get_result_of_notice_html(check_notice_html, check_notice_file_exist_at_path)
        except Exception as error:
            logger.debug(f"find_notice_html error:{error}")
    return_list.extend(bin_info)


def map_binary_module_name_and_path(installed_file_list):
    global final_bin_info

    for out_binary in installed_file_list:
        file_name_with_relative_path = out_binary.replace(build_out_path + "/", "")
        if "obj/STATIC_LIBRARIES/" in file_name_with_relative_path:
            file_name_with_relative_path = os.path.basename(file_name_with_relative_path)
        file_name = os.path.basename(file_name_with_relative_path)
        index_of_dot = file_name.rfind('.')
        if index_of_dot > -1:
            module_name = file_name[:index_of_dot]
        else:
            module_name = file_name

        found_json_obj = get_module_json_obj_by_installed_path(module_name, file_name_with_relative_path, file_name)
        bin_info = AndroidBinary(file_name_with_relative_path)
        bin_info.set_bin_name_with_installed_path(out_binary)
        if found_json_obj != "":
            if found_json_obj["path"] != "" and len(found_json_obj["path"]) > 0:
                bin_info.set_source_code_path(found_json_obj["path"][0])
                bin_info.set_module_name(found_json_obj[MODULE_TYPE_NAME])
            else:
                bin_info.set_module_name(found_json_obj[MODULE_TYPE_NAME])
        else:
            bin_info.set_module_name(module_name)

        final_bin_info.append(bin_info)


def check_already_exist(bin):
    items = list(filter(lambda x: x.bin_name is bin, final_bin_info))
    return len(items) > 0


def filter_non_path_bin(FIND_DIRECTORY_MODE):
    global final_bin_info
    filter_file_type = ['.oat', '.art', '.hyb', '.dat', '.xml', '.odex', '.sh']
    bin_info_list = final_bin_info[:]
    need_to_find = {}

    for item in bin_info_list:
        try:
            bin_name = item.bin_name
            path = item.source_code_path
            output = os.path.join(build_out_path, bin_name)
            filename, file_extension = os.path.splitext(bin_name)
            if path == CONST_NULL:
                if file_extension in filter_file_type:
                    final_bin_info.remove(item)
                elif os.path.islink(output):
                    real_bin = os.path.realpath(output)
                    if real_bin is not None:
                        idx = real_bin.find(build_out_path)
                        final_bin = real_bin[idx:].replace(build_out_path, '')
                        if check_already_exist(final_bin):
                            final_bin_info.remove(item)
                else:
                    need_to_find[os.path.basename(bin_name)] = []
        except Exception:
            pass

    if FIND_DIRECTORY_MODE:
        get_path_by_using_find(need_to_find, build_out_path, f"FIND_RESULT_OF_BINARIES_{now}.txt", python_script_dir)


def search_binaries_by_bin_name_and_checksum(bin_name_to_search, bin_checksum_to_search):
    bin_list_same_names = []
    bin_cnt = 0
    result = False
    bin_name_without_path = os.path.basename(bin_name_to_search)
    for item in final_bin_info:
        bin_name = os.path.basename(item.bin_name)
        checksum = item.checksum
        if bin_name == bin_name_without_path and checksum == bin_checksum_to_search:
            bin_list_same_names.append(item)
            bin_cnt += 1

    if bin_cnt > 1:
        result = True

    return result, bin_list_same_names


def get_repositories_name_from_json():
    repositories = {}
    repository_file = os.path.join("resources", "aosp_repository.json")

    try:
        base_dir = sys._MEIPASS
    except Exception:
        base_dir = os.path.dirname(__file__)

    file_withpath = os.path.join(base_dir, repository_file)
    try:
        with open(file_withpath, 'r') as f:
            repositories = json.load(f)
    except Exception as ex:
        logger.debug('Error to get repository list from json file :' + str(ex))

    return repositories


def get_repositories_name_from_web():
    repositories = {}
    urls = ["https://android.googlesource.com/platform/", "https://android.googlesource.com/"]

    for url in urls:
        try:
            html = urllib.request.urlopen(url)
            source = html.read()
            html.close()

            soup = BeautifulSoup(source, "lxml")

            pkg_list = soup.findAll("span", "RepoList-itemName")

            for pkg in pkg_list:
                repositories[pkg.text] = url + pkg.text
        except Exception:
            pass

    return repositories


def get_repositories_name():
    global repositories
    success = False
    repositories = {}
    remote_is_aosp = False

    # Get repository name from manifest first.
    read_success, manifest_content = read_file(".repo/manifest.xml", True)
    if read_success:
        soup = BeautifulSoup(manifest_content, "lxml")
        for remote_info in soup.findAll("remote"):
            if str(remote_info['review']).find("android-review.googlesource.com") > -1:  # Only in case of aosp
                remote_is_aosp = True
                break

        if remote_is_aosp:
            for project_item in soup.findAll("project"):
                repositories[project_item['path']] = ""

    if (not read_success) or (not remote_is_aosp) or repositories is None:  # Get repository name from web.
        repositories = get_repositories_name_from_web()
    if len(repositories) == 0:
        repositories = get_repositories_name_from_json()
    if len(repositories):
        success = True
    return success


def set_mk_file_path():
    global final_bin_info
    cwd = os.getcwd() + "/"
    for item in final_bin_info:
        local_path = item.source_code_path
        mk_path = local_path

        idx = local_path.find("/..")
        if idx > -1:
            abs_path = os.path.realpath(local_path)
            abs_path = abs_path.replace(cwd, "")
            item.source_code_path = abs_path
            mk_path = local_path[:idx]

        item.set_mk_file_path(mk_path)


def remove_from_the_list(remove_list_file):
    remove_list = {}
    remove_tlsh_list = {}
    if remove_list_file == "":
        return remove_list, remove_tlsh_list
    try:
        if remove_list_file != os.path.abspath(remove_list_file):
            remove_list_file = os.path.join(python_script_dir, remove_list_file)

        if os.path.isfile(remove_list_file):
            read_success, read_line = read_file(remove_list_file)
            if read_success:
                for line in read_line:
                    try:
                        cell_list = line.split("\t")
                        bin_name = cell_list[0]
                        bin_name_to_search = os.path.basename(bin_name)
                        bin_tlsh = cell_list[8]
                        bin_checksum = cell_list[9].strip()
                        remove_list[bin_checksum + bin_name_to_search] = ""
                        item = remove_tlsh_list.get(bin_name_to_search)
                        if item:
                            item.append(bin_tlsh)
                        else:
                            remove_tlsh_list[bin_name_to_search] = [bin_tlsh]

                    except Exception as error:
                        logger.error(f"Parsing line :{error}")
            else:
                logger.warning(f"Failed to read {remove_list_file}")
        else:
            logger.debug(f"Can't find a file to remove: {remove_list_file}")
    except Exception as error:
        logger.error(f"Remove files :{error}")

    return remove_list, remove_tlsh_list


def set_checksum_tlsh_and_get_oss_from_db_after_remove_duplication(remove_list_file=""):
    global final_bin_info

    return_list = do_multi_process(get_checksum_tlsh, final_bin_info)
    final_bin_info = return_list[:]
    remove_duplicated_binaries_by_checking_checksum(remove_list_file)

    func = partial(get_oss_info_from_db, platform_version)
    return_oss_list = do_multi_process(func, final_bin_info)
    final_bin_info = return_oss_list[:]


def get_checksum_tlsh(bin_info_list, return_bin_list):
    for item in bin_info_list:
        tlsh_value = CONST_TLSH_NULL
        checksum_value = ""

        try:
            bin_file_full_path = item.bin_name_with_installed_path
            if not os.path.exists(bin_file_full_path):
                pass

            f = open(bin_file_full_path, "rb")
            byte = f.read()
            sha1_hash = hashlib.sha1(byte)
            checksum_value = sha1_hash.hexdigest()
            tlsh_value = tlsh.hash(byte)
            f.close()
        except Exception:
            pass
        if tlsh_value == "":
            tlsh_value = CONST_TLSH_NULL

        item.set_tlsh(tlsh_value)
        item.set_checksum(checksum_value)

    return_bin_list.extend(bin_info_list)


def remove_duplicated_binaries_by_checking_checksum(remove_list_file):
    global final_bin_info
    result_file_name = f"REMOVED_BIN_BY_DUPLICATION_{now}.txt"
    str_bin_removed = ""
    filtered_binaries = []
    checked_file_name = {}
    cnt = 0
    remove_list, remove_tlsh_list = remove_from_the_list(remove_list_file)

    for item in final_bin_info[:]:
        bin_name_to_search = os.path.basename(item.bin_name)
        bin_checksum = item.checksum
        search_key = bin_checksum + bin_name_to_search

        skip = search_key in remove_list
        if not skip:
            tlsh_items = remove_tlsh_list.get(bin_name_to_search)
            if tlsh_items:
                bin_tlsh = item.tlsh
                for value in tlsh_items:
                    tlsh_diff = tlsh.diff(bin_tlsh, value)
                    if tlsh_diff <= 120:
                        skip = True
                        continue
        if skip:
            cnt += 1
            print_removed_str = item.get_print_array(False)
            for row_removed in print_removed_str:
                str_bin_removed += f"{row_removed}\n"
            continue
        elif search_key not in checked_file_name:
            find_result, same_name_binaries = search_binaries_by_bin_name_and_checksum(item.bin_name,
                                                                                       bin_checksum)
            checked_file_name[search_key] = find_result

            if find_result:
                final_added = ""  # finally added binary
                # 0 : file in system folder, 1: Source Path exists, 2:exist in NOTICE.html, 3: shortest path
                priority = ["", "", "", ""]
                idx_notice = 2
                value_notice = ""
                for bin_same_name in same_name_binaries:
                    bin_with_path = bin_same_name.bin_name
                    notice_check = bin_same_name.notice
                    src_path = bin_same_name.source_code_path

                    if bin_with_path.startswith('system/'):
                        priority[0] = return_shorter_installed_path_data(priority[0], bin_same_name)
                    if src_path is not None and len(src_path) > 0:
                        priority[1] = return_shorter_installed_path_data(priority[1], bin_same_name)
                    if notice_check == "ok(NA)" or notice_check == "ok":
                        value_notice = notice_check
                        priority[idx_notice] = return_shorter_installed_path_data(priority[idx_notice],
                                                                                  bin_same_name)

                    priority[3] = return_shorter_installed_path_data(priority[3], bin_same_name)

                for i in range(len(priority)):
                    if priority[i] != "":
                        if final_added == "":
                            final_added = priority[i]
                            if i != idx_notice and final_added.notice.find(
                                    "nok") > -1 and value_notice != "":
                                # If same binary is included in NOTICE.html, change the NOTICE value to "ok"
                                final_added.set_notice(value_notice)
                            filtered_binaries.append(final_added)
                            break

                for bin_same_name in same_name_binaries:
                    if bin_same_name.bin_name != final_added.bin_name:
                        print_removed_str = bin_same_name.get_print_array(False)
                        for row_removed in print_removed_str:
                            str_bin_removed += f"{row_removed}\n"
            else:  # Don't have any duplicated binaries
                filtered_binaries.append(item)
    if remove_list_file != "":
        logger.warning(f"Number of files removed due to -r option result.txt: {cnt}")
    # Replace final binary list
    final_bin_info = filtered_binaries[:]

    # Write removed binary list to text file
    if str_bin_removed != "":
        write_txt_file(result_file_name, str_bin_removed, python_script_dir)


def return_shorter_installed_path_data(origin, new):
    if origin == "" or not hasattr(origin, 'bin_name'):
        return new
    elif new == "" or not hasattr(new, 'bin_name'):
        return origin
    else:
        origin_path = origin.bin_name
        new_path = new.bin_name

        if len(origin_path) > len(new_path):
            return new
        elif len(origin_path) == 0:
            return new
    return origin


def set_oss_name_by_repository():
    global final_bin_info
    success = get_repositories_name()
    if success:
        for item in final_bin_info:
            try:
                oss_name = item.oss_name
                source_path = item.source_code_path
                item_license = item.license
                if (oss_name == CONST_NULL or oss_name == "Android Open Source Project") and source_path != CONST_NULL:
                    if item_license not in skip_license:
                        item.oss_name, item.oss_version, item.download_location = get_oss_component_name(source_path, oss_name, item.oss_version)
                        item.homepage = item.download_location
            except Exception as error:
                logger.debug(f"Set OSS Name:{error}")


def find_meta_lic_files():
    global meta_lic_files
    dir = os.path.join(build_out_path, "obj")
    for current_dir_path, current_subdirs, current_files in os.walk(dir):
        for aFile in current_files:
            if aFile.endswith(".meta_lic"):
                key = aFile.replace(".meta_lic", "")
                read_success, meta_lic_lines = read_file(os.path.join(current_dir_path, aFile))
                if read_success:
                    lic = ""
                    lic_list = []
                    for line in meta_lic_lines:
                        try:
                            line = line.strip()
                            pattern = re.compile(r'license_kinds:\s*"([\s\S]+)"')
                            matched = pattern.match(line)
                            if matched is not None:
                                matched = matched.group(1)
                                if not matched.startswith("legacy_"):
                                    matched = matched.replace("SPDX-license-identifier-", "")
                                    if matched:
                                        lic_list.append(matched)
                        except Exception as error:
                            logger.warn(f"meta_lic_files:{error}")
                    if lic_list:
                        lic = ','.join(lic_list)
                        meta_lic_files[key] = lic


def main():
    global android_log_lines, ANDROID_LOG_FILE_NAME, NOTICE_HTML_FILE_NAME, python_script_dir, num_cores, now, logger, final_bin_info
    find_empty_path = False
    _create_additial_notice = False
    notice_check_ok = False
    base_binary_txt = ""
    auto_fill_oss_name = True
    _NOTICE_CHECKLIST_TYPE = False
    analyze_source = False
    path_to_exclude = []
    RESULT_FILE_EXTENSION = ".xlsx"

    num_cores = multiprocessing.cpu_count() - 1
    if num_cores < 1:
        num_cores = 1

    python_script_dir = os.getcwd()
    android_src_path = python_script_dir
    now = datetime.now().strftime('%y%m%d_%H%M')
    log_txt_file = os.path.join(python_script_dir, f"fosslight_log_android_{now}.txt")
    result_excel_file_name = os.path.join(python_script_dir, f"fosslight_report_android_{now}")
    remove_list_file = ""

    parser = argparse.ArgumentParser(description='FOSSLight Android', prog='fosslight_android', add_help=False)
    parser.add_argument('-h', '--help', action='store_true', required=False)
    parser.add_argument('-v', '--version', action='store_true', required=False)
    parser.add_argument('-s', '--source', type=str, required=False)
    parser.add_argument('-b', '--binary', type=str, required=False)
    parser.add_argument('-n', '--notice', type=str, required=False)
    parser.add_argument('-t', '--toadd', action='store_true', required=False)
    parser.add_argument('-m', '--more', action='store_true', required=False)
    parser.add_argument('-c', '--check', type=str, required=False)
    parser.add_argument('-a', '--android', type=str, required=False)
    parser.add_argument('-f', '--find', action='store_true', required=False)
    parser.add_argument('-i', '--ignore', action='store_true', required=False)
    parser.add_argument('-p', '--packaging', type=str, required=False)
    parser.add_argument('-d', '--divide', type=str, required=False)
    parser.add_argument('-r', '--remove', type=str, required=False)
    parser.add_argument('-e', '--exclude', nargs="*", required=False, default=[])

    args = parser.parse_args()
    if args.help:
        print_help_msg()
    if args.version:
        print_version(PKG_NAME)
    if args.source:  # android source path
        os.chdir(args.source)
        android_src_path = args.source
    if args.binary:  # Base model's binary.txt to exclude
        base_binary_txt = args.binary
    if args.notice:
        NOTICE_HTML_FILE_NAME = args.notice
    if args.toadd:  # Create needtoadd-notice.html file.
        _create_additial_notice = True
    if args.more:  # Analyze source mode.
        analyze_source = True
    if args.check:
        _NOTICE_CHECKLIST_TYPE = True
        notice_check_ok = (args.check == "ok" or args.check == "OK")
    if args.android:
        ANDROID_LOG_FILE_NAME = args.android
    if args.find:  # Execute "find" command when source path is not found.
        find_empty_path = True
    if args.ignore:  # Disable the function to automatically convert OSS names based on AOSP.
        auto_fill_oss_name = False
    if args.exclude:  # Path to exclude from source code analysis.
        path_to_exclude = args.exclude

    logger, result_log = init_log(log_txt_file, True, logging.INFO, logging.DEBUG, PKG_NAME)

    if args.packaging:
        check_packaging_files(args.packaging)
        return
    if args.divide:
        divide_notice_files_by_binary(args.divide, python_script_dir, now)
        return
    if args.remove:  # Remove the inputted list from the binary list.
        remove_list_file = args.remove

    if _NOTICE_CHECKLIST_TYPE:
        run_notice_html_checklist(base_binary_txt, notice_check_ok, NOTICE_HTML_FILE_NAME)
        return

    read_success, android_log_lines = read_file(ANDROID_LOG_FILE_NAME)
    if not read_success:
        logger.error("(-a option) Fail to read a file:" + ANDROID_LOG_FILE_NAME)
        sys.exit(1)
    else:
        set_env_variables_from_result_log()

    map_binary_module_name_and_path(find_binaries_from_out_dir())

    notice_files = find_notice_value()
    find_bin_license_info()

    set_mk_file_path()  # Mk file path and local path, location of NOTICE file, can be different
    filter_non_path_bin(find_empty_path)

    set_checksum_tlsh_and_get_oss_from_db_after_remove_duplication(remove_list_file)

    if auto_fill_oss_name:
        set_oss_name_by_repository()
    if analyze_source:
        from ._src_analysis import find_item_to_analyze
        final_bin_info = find_item_to_analyze(final_bin_info, python_script_dir, now, path_to_exclude)

    scan_item = ScannerItem(PKG_NAME, now)
    scan_item.set_cover_pathinfo(android_src_path, "")

    scan_item.set_cover_comment(f"Total number of binaries: {len(final_bin_info)}")
    scan_item.set_cover_comment(f"\nNotice: {notice_files}")
    scan_item.append_file_items(final_bin_info, PKG_NAME)
    success, msg, result_file = write_output_file(result_excel_file_name, RESULT_FILE_EXTENSION,
                                                  scan_item, HEADER, HIDDEN_HEADER)
    if not success:
        logger.warning(f"Failed to write result to excel:{msg}")
    result_log["Output FOSSLight Report"] = f"{result_file}"

    if _create_additial_notice:
        create_additional_notice(final_bin_info, python_script_dir)

    # Print the result
    result_log["Output Directory"] = python_script_dir
    try:
        str_final_result_log = yaml.safe_dump(result_log, allow_unicode=True, sort_keys=True)
        logger.info(str_final_result_log)
    except Exception as ex:
        logger.warning(f"Failed to print result log. : {ex}")


if __name__ == "__main__":
    main()
