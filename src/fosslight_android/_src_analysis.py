#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging
import os
from fosslight_source.run_scancode import run_scan as source_analysis
from fosslight_source.cli import create_report_file, merge_results
from ._common import CONST_NULL
from fosslight_util.constant import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)
ANALYSIS_OUTPUT_DIR = "source_analyzed"


def find_item_to_analyze(bin_info, output_path, start_time="", path_to_exclude=[]):
    path_list_to_analyze = {}
    for item in bin_info:
        try:
            source_path = item.source_code_path
            item_license = item.license
            if item_license == CONST_NULL and source_path != CONST_NULL:
                path_list_to_analyze[source_path] = ""
        except Exception as error:
            logger.debug(f"Find_item_to_analyze:{error}")

    source_analysis_path = [path for path in path_list_to_analyze.keys() if path not in path_to_exclude]
    if source_analysis_path:
        logger.info(f"|--Source analysis for {len(source_analysis_path)} paths.")
        for path in source_analysis_path:
            file_array = [len(files) for r, d, files in os.walk(path)]
            files = sum(file_array)
            logger.debug(f"{path}, File Count:{files}")

        output_dir = os.path.join(output_path, f"{ANALYSIS_OUTPUT_DIR}_{start_time}")

        logger.info("********* START TO ANALYZE SOURCE **********")
        idx = 0
        for source_path in source_analysis_path:
            try:
                idx += 1
                if os.path.isdir(source_path):
                    logger.info(f"({idx}){source_path}")
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
                logger.debug(f"Failed to update license from src analysis:{error}")

    return bin_info


def run_src_analysis(scan_input_path, start_time="", output_dir=""):
    license = CONST_NULL
    if os.path.exists(scan_input_path):
        try:
            output_file_name = scan_input_path.replace("/", "_")
            success, result_log, result, matched_txt = source_analysis(os.path.abspath(scan_input_path),
                                                                       output_file_name,
                                                                       False, -1, True, True, "",
                                                                       True)
            result = merge_results(result)
            if success:
                license_list = []
                for scan_item in result:
                    license_list.extend(scan_item.licenses)
                license_list = list(dict.fromkeys(license_list))
                license = ",".join(license_list)
                if result:
                    logger.debug(f"Create a report - source analysis :{output_dir}/{output_file_name}.xlsx")
                    create_report_file(start_time, result, matched_txt, [], 'scancode',
                                       True, output_dir, [output_file_name], [".xlsx"], False, "", scan_input_path, "", ["excel"])
            else:
                logger.debug(f"Failed to analysis (scan) {scan_input_path}:{result_log}")
        except Exception as error:
            logger.debug(f"Failed to analysis {scan_input_path}:{error}")
    return license
