#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging
import os
from fosslight_source.run_scancode import run_scan as source_analysis
from fosslight_source.cli import create_report_file
from ._common import CONST_NULL
from fosslight_util.constant import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)
ANALYSIS_OUTPUT_DIR = "source_analyzed"


def find_item_to_analyze(bin_info, output_path, start_time=""):
    logger.info("* START TO ANALYZE SOURCE")
    path_list_to_analyze = {}
    for item in bin_info:
        try:
            source_path = item.source_code_path
            item_license = item.license
            if item_license == CONST_NULL and source_path != CONST_NULL:
                path_list_to_analyze[source_path] = ""
        except Exception as error:
            logger.debug(f"Find_item_to_analyze:{error}")

    logger.info(f"|--Source analysis begins for {len(path_list_to_analyze)} paths.")
    idx = 0
    output_dir = os.path.join(output_path, f"{ANALYSIS_OUTPUT_DIR}_{start_time}")
    for source_path in path_list_to_analyze.keys():
        try:
            idx += 1
            logger.info(f"|---{idx} {source_path}")
            license = run_src_analysis(source_path, start_time, output_dir)
            path_list_to_analyze[source_path] = license
        except Exception as error:
            logger.debug(f"Failed to run src analysis:{error}")

    for analyzed_path, analyzed_license in path_list_to_analyze.items():
        try:
            for item in bin_info:
                source_path = item.source_code_path
                item_license = item.license
                if source_path == analyzed_path and item_license == CONST_NULL:
                    item.set_license(analyzed_license)
        except Exception as error:
            logger.debug(f"failed to update license from src analysis:{error}")

    return bin_info


def run_src_analysis(scan_input_path, start_time="", output_dir=""):
    license = CONST_NULL
    if os.path.exists(scan_input_path):
        try:
            success, result_log, result, matched_txt = source_analysis(os.path.abspath(scan_input_path),
                                                                       output_dir,
                                                                       False, -1, True, True, "",
                                                                       True)
            if success:
                output_file_name = scan_input_path.replace("/", "_")
                license_list = []
                for scan_item in result:
                    license_list.extend(scan_item.licenses)
                license_list = list(dict.fromkeys(license_list))
                license = ",".join(license_list)
                if result:
                    create_report_file(start_time, result, matched_txt, "scancode", True,
                                       output_dir, output_file_name, ".xlsx")
            else:
                logger.debug(f"Failed to analysis (scan) {scan_input_path}:{result_log}")
        except Exception as error:
            logger.debug(f"Failed to analysis {scan_input_path}:{error}")
    return license