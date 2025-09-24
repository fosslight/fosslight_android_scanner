#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from bs4 import BeautifulSoup
from ._util import read_file, write_txt_file
from ._common import NOTICE_FILE_NAME
from fosslight_util.constant import LOGGER_NAME
import re
import gzip
import shutil

logger = logging.getLogger(LOGGER_NAME)
CANNOT_FIND_MSG = "CANNOT_FIND_NOTICE_HTML"


def run_notice_html_checklist(binary_file, check_type, notice_file):
    notice_file_list = {}  # File list in NOTICE.html
    # Read a binary file
    read_success, binaries = read_file(binary_file)
    if read_success:
        try:
            notice_file_list, notice_files = read_notice_file("", notice_file)
            if not notice_file_list:  # Empty
                logger.info(CANNOT_FIND_MSG)
                return
            for item in binaries:
                try:
                    output = item.strip()
                    if output != "":
                        if find_bin_in_notice(output, notice_file_list):  # ok
                            if not check_type:
                                logger.warn(f"{output} ok")
                        else:  # nok
                            if check_type:
                                logger.warn(f"{output} nok")
                except Exception as error:
                    logger.info(f"Find bin in NOTICE :{error}")
        except IOError:
            logger.info(CANNOT_FIND_MSG)
    else:
        logger.info(f"Fail to read a binary file: {binary_file}")
    return notice_file_list


def find_bin_in_notice(binary_file_name, notice_file_list):
    notice_found = False
    if binary_file_name:
        if binary_file_name in notice_file_list:
            notice_found = True
        else:
            apex_name_search_list = []
            try:
                apex_name = ""
                m = re.search(r"apex\/([^\/]+)\/", binary_file_name)
                if m:
                    apex_name = m.group(1)
                if apex_name:
                    apex_name_search_list = [f"{apex_name}.apex", f"{apex_name}.capex",
                                             f"{apex_name}_compressed.apex", f"{apex_name}-uncompressed.apex"]
            except Exception as error:
                logger.debug(f"find_bin_in_notice :{error}")
            binary_without_path = os.path.basename(binary_file_name)
            for key in notice_file_list:
                key_file_name = os.path.basename(key)
                if key_file_name == binary_without_path or any(apex_name == key_file_name for apex_name in apex_name_search_list):
                    notice_found = True
                    break

    return notice_found


def find_files_by_extension(path):
    extensions = ['.html', '.xml']
    GZ_EXTENSION = '.gz'
    files = []
    try:
        gz_files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(GZ_EXTENSION)]
        for gz_file in gz_files:
            unzip_file = gz_file.replace('.gz', '')
            if not os.path.isfile(unzip_file):
                with gzip.open(gz_file, 'rb') as f_in:
                    with open(unzip_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
    except Exception as error:
        logger.info(f"Fail unzip gz file:{error}")

    for extension in extensions:
        files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(extension)]
        if len(files) > 0:
            break

    return files


def read_notice_file(notice_file_path):
    final_notice_file = {}
    # NOTICE.html need to be skipped the errors related to decode
    encodings = ["latin-1", "utf-8", "utf-16"]
    notice_files = []

    if os.path.isfile(notice_file_path):
        notice_files.append(notice_file_path)
        if notice_file_path.endswith((".xml", ".html", ".txt", "xml.gz")):
            notice_file_path = os.path.dirname(notice_file_path)

    if os.path.isdir(notice_file_path):
        additional_notice_files = find_files_by_extension(notice_file_path)
        if len(additional_notice_files) > 0:
            notice_files.extend(additional_notice_files)
            notice_files = list(set(notice_files))

    for file_name in notice_files:
        file_list = {}
        file_content = ""
        if os.path.isfile(file_name):
            for encoding_option in encodings:
                try:
                    file = open(file_name, encoding=encoding_option)
                    file_content = file.read()
                    file.close()
                    if file_content != "":
                        break
                except Exception:
                    pass
            if file_content != "":
                try:
                    if file_name.endswith("xml"):
                        file_list = parsing_notice_xml_format(file_content)
                    else:
                        file_list = parsing_notice_html_format(file_content)
                except Exception as error:
                    logger.info("Can't read a notice. :" + file_name)
                    logger.info(f"{error}")
                final_notice_file.update(file_list)
            else:
                logger.info(f"Notice file is empty. :{file_name}")

    return final_notice_file, notice_files


def parsing_notice_xml_format(notice_file_content):
    file_list = {}
    soup = BeautifulSoup(notice_file_content, "lxml")

    for e in soup.findAll("file-name"):  # NOTICE.xml
        line = e.text.strip()
        if line.startswith('/'):
            line = line[1:]
        file_list[line] = ""

    return file_list


def parsing_notice_html_format(notice_file_content):
    file_list = {}
    soup = BeautifulSoup(notice_file_content, "lxml")

    for e in soup.findAll('br'):  # NOTICE.html
        e.extract()

    str_file_list = []
    mydivs = soup('div', {'class': 'file-list'})  # NOTICE.html
    for div in mydivs:
        str_file_list.append(str(div.prettify()))
    strong_list = soup.find_all('strong')
    for strong in strong_list:
        str_file_list.append(strong.text)
    uls = soup.find_all("ul", "file-list")
    for ul in uls:
        for li in ul.findAll('li'):
            str_file_list.append(li.text)

    for str_div in str_file_list:
        for line in str_div.split():
            if line.find('<') < 0 and line.find('>') < 0:
                line = line.strip()
                line = line.replace('//', '/')
                if line.startswith('/'):
                    line = line[1:]
                file_list[line] = ""

    mydivs = soup('span', {'lang': 'EN-US'})  # Exceptional case for MC <span lang=EN-US>
    if mydivs != "" and mydivs is not None:
        for div in mydivs:
            str_div = str(div.prettify())
            for line in str_div.splitlines():
                if line.find('<') < 0 and line.find('>') < 0:
                    line = line.replace("&nbsp;", "")
                    line = line.strip()
                    if line.startswith('/'):
                        line = line[1:]
                    if line != "" and line.find(" ") < 0:
                        file_list[line] = ""

    return file_list


def create_additional_notice(bin_info_list, result_file_path):
    # Create lge_notice.html file for nok(NA)
    # This file will be placed under build/tools/

    logger.info("---------CREATE ADDITIONAL NOTICE-----------")

    lge_notice_body_str = ""
    lge_notice_file_name = "needtoadd-notice.html"
    lge_notice_head = "<table cellpadding=\"0\" cellspacing=\"0\" border=\"0\">"
    lge_notice_tail = "</table>"

    # Binary list that failed to create it into the lge notice
    fail_to_create_lge_notice = ""

    # Grouping by notice file
    nok_na_list = {}

    for item in bin_info_list:
        if item.notice == "ok":
            notice_file = os.path.join(item.source_code_path, NOTICE_FILE_NAME)
            if os.path.isfile(notice_file):
                if notice_file in nok_na_list:
                    nok_na_list[notice_file].append(item.bin_name)
                else:
                    nok_na_list[notice_file] = [item.bin_name]
            else:
                fail_to_create_lge_notice += str(item) + "\n"

    for key, value in nok_na_list.items():
        noti_txt = get_binary_notice_text(value, key)
        if noti_txt == "":
            fail_to_create_lge_notice += str(value) + "\n"
        else:
            lge_notice_body_str += noti_txt

    # Write NOTICE as a file
    if lge_notice_body_str != "":
        final_notice = lge_notice_head + lge_notice_body_str + lge_notice_tail
        write_txt_file(lge_notice_file_name, final_notice, result_file_path)

    if fail_to_create_lge_notice != "":
        write_txt_file(lge_notice_file_name + "_failed", fail_to_create_lge_notice, result_file_path)


def get_binary_notice_text(binary_file_array, notice_file_path):
    try:
        # Per binary file
        lge_notice_body_start = "<tr id=\"id0\"><td class=\"same-license\">\
                                 <div class=\"label\">Notices for file(s):</div>\
                                 <div class=\"file-list\">"
        # Append binary_file_name + <br/>
        lge_notice_body_middle = "</div><!-- file-list --><pre class=\"license-text\">"
        # Append license test
        lge_notice_body_tail = "</pre><!-- license-text --></td></tr><!-- same-license -->"

        # File list
        noti_txt = lge_notice_body_start
        binary_file_array = list(set(binary_file_array))
        for bin_file in binary_file_array:
            noti_txt += bin_file
            noti_txt += "<br/>"
        noti_txt += lge_notice_body_middle

        # License text
        f = open(notice_file_path, 'r')
        notice_text = f.read()
        f.close()
        noti_txt += notice_text
        noti_txt += lge_notice_body_tail

        return noti_txt
    except Exception:
        return ""


def divide_notice_files_by_binary(notice_file_to_divide, result_file_path, now):
    read_success, contents = read_file(notice_file_to_divide, True)
    if read_success:
        dir_name = f"NOTICE_FILES_{now}"
        dir_name = os.path.join(result_file_path, dir_name)
        try:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            else:
                logger.warn(f"{dir_name} folder already exists.")
        except OSError:
            logger.warn(f"Cannot create {dir_name} folder.")
            return
        os.chdir(dir_name)
        items = parsing_notice_html_for_license_text(contents)
        create_license_txt_files(items, "")
        logger.warn(f"{dir_name} folder has been created.")
    else:
        logger.warn(f"Failed to read: {notice_file_to_divide}")


def create_license_txt_files(file_list, result_file_path):
    try:
        for file in file_list:
            dir = file['path']
            file_name = file['name']

            if dir != "" and not os.path.exists(dir):
                os.makedirs(dir)
            write_txt_file(file_name, file['license_txt'], "")
    except Exception as error:
        logger.warn(f"Error: Cannot create a notice file.:{error}")


def parsing_notice_html_for_license_text(notice_file_content):
    file_list = []
    soup = BeautifulSoup(notice_file_content, 'lxml')
    tds = soup.findAll('tr')

    for td in tds:
        try:
            if td is not None:
                td_soup = BeautifulSoup(str(td), 'lxml')
                files = td_soup.find('div', {'class': 'file-list'})
                soup2 = BeautifulSoup(str(files), 'lxml')
                file_plain_text = soup2.get_text(separator="\n")
                license_txt = td_soup.find('pre', {'class': 'license-text'})
                license_txt_without_tag = license_txt.get_text()
                if license_txt is None:
                    logger.info("Error: Can't find license text of " + str(td))
                    continue
                for file in file_plain_text.splitlines():
                    file = file.strip()
                    if file != "":
                        if file.startswith("/"):
                            file = file[1:]
                        file_item = {'name': file + ".txt", 'path': os.path.dirname(file),
                                     'license_txt': str(license_txt_without_tag)}
                        file_list.append(file_item)
        except UnicodeEncodeError:
            continue
    return file_list
