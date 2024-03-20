#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import sys
import xlsxwriter
import logging
from fosslight_util.write_txt import write_txt_file
from fosslight_util.constant import LOGGER_NAME
from fosslight_util.write_excel import hide_column

logger = logging.getLogger(LOGGER_NAME)
HIDDEN_HEADER = ['TLSH', 'SHA1']


def write_result_to_excel(out_file_name, row_list):
    header_row = ['ID', 'Binary Name', 'Source Code Path', 'NOTICE.html', 'OSS Name', 'OSS Version', 'License',
                  'Download Location', 'Homepage',
                  'Copyright Text',
                  'License Text', 'Exclude', 'Comment', 'Need Check', 'TLSH', 'SHA1']
    sheet_name = "BIN (Android)"
    try:
        workbook = xlsxwriter.Workbook(out_file_name)
        worksheet = create_worksheet(workbook, sheet_name, header_row)
        write_result_to_sheet(worksheet, row_list)
        hide_column(worksheet, header_row, HIDDEN_HEADER)
        workbook.close()
    except Exception as ex:
        print('* Error :' + str(ex))


def write_result_to_sheet(worksheet, list_to_print):
    row = 1
    for row_item in list_to_print:
        worksheet.write(row, 0, row)
        for col_num, value in enumerate(row_item):
            worksheet.write(row, col_num + 1, value)
        row += 1


def create_worksheet(workbook, sheet_name, header_row):
    worksheet = workbook.add_worksheet(sheet_name)
    for col_num, value in enumerate(header_row):
        worksheet.write(0, col_num, value)
    return worksheet


def write_result_to_txt_and_excel(out_excel_file, final_bin_info, out_txt_file):
    excel_list = []
    final_str = ['Binary Name\tSource Code Path\tNOTICE.html\tOSS Name\tOSS Version\tLicense\tNeed '
                 'Check\tComment\ttlsh\tchecksum']
    if final_bin_info:
        for item in sorted(final_bin_info, key=lambda binary: (binary.source_code_path, binary.bin_name)):
            try:
                print_row, print_excel = item.get_print_items()
                final_str.append('\n'.join(print_row))
                excel_list.extend(print_excel)
            except Exception as error:
                logger.error(f"Get results to print:{error}")
                sys.exit(1)

        success, error_msg = write_txt_file(out_txt_file, '\n'.join(final_str))
        write_result_to_excel(out_excel_file, excel_list)
    else:
        logger.warning("Nothing is detected from the scanner so output file is not generated.")
