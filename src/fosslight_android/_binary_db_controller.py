#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging
import os
import psycopg2
import pandas as pd
import tlsh
from ._common import CONST_TLSH_NULL
from fosslight_util.constant import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)
columns = ['filename', 'pathname', 'checksum', 'tlshchecksum', 'ossname', 'ossversion', 'license', 'platformname',
           'platformversion']

DB_USER = 'bin_analysis_script_user'
DB_PSWD = 'script_123'


def connect_to_lge_bin_db():
    conn = ""
    cur = ""
    user = DB_USER
    password = DB_PSWD
    host_product = 'bat.lge.com'
    dbname = 'bat'
    port = '5432'

    connection_string = "dbname={dbname} user={user} host={host} password={password} port={port}" \
        .format(dbname=dbname,
                user=user,
                host=host_product,
                password=password,
                port=port)
    try:
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()
    except Exception:
        conn = ""
        cur = ""
    return conn, cur


def get_oss_info_from_db(platform_version, bin_info_list, return_list):

    conn, cur = connect_to_lge_bin_db()
    if conn != "" and cur != "":
        for item in bin_info_list:
            try:
                checksum_value = item.checksum
                tlsh_value = item.tlsh
                bin_file = item.bin_name
                bin_file_name = os.path.basename(bin_file)
                # Get OSS Information From Binary DB by matching checksum , filename, tlsh
                df_result, item_comment, is_new = get_oss_info_by_tlsh_and_filename(bin_file_name,
                                                                                    checksum_value, tlsh_value,
                                                                                    item.source_code_path,
                                                                                    platform_version, conn, cur)
                item.set_comment(item_comment)
                item.is_new_bin = is_new
                if df_result is not None and len(df_result) > 0:
                    for idx, row in df_result.iterrows():
                        if idx == 0:
                            item.set_oss_name(row['ossname'])
                            item.set_oss_version(row['ossversion'])
                            item.set_license(row['license'])
                        else:  # In case more than 2 OSS is used for this bin.
                            item.set_additional_oss_items(row['ossname'] + '\t' + row['ossversion'] + '\t' + row['license'])
            except Exception as error:
                logger.warn(f"READ OSS :{error}")

        disconnect_lge_bin_db(conn, cur)
    return_list.extend(bin_info_list)


def get_oss_info_by_tlsh_and_filename(file_name, checksum_value, tlsh_value, source_path, platform_version, conn, cur):
    sql_statement = "SELECT filename,pathname,checksum,tlshchecksum,ossname,ossversion,license,platformname,platformversion FROM lgematching "
    sql_statement_checksum = " WHERE filename=%(fname)s AND checksum=%(checksum)s;"
    sql_checksum_params = {'fname': file_name, 'checksum': checksum_value}
    sql_statement_filename = "SELECT tlshchecksum FROM lgematching WHERE filename=%(fname)s AND tlshchecksum <> '0' ORDER BY ( " \
                             "CASE " \
                             "WHEN sourcepath = %(src_path)s AND lower(platformname)=%(plat_name)s " \
                             "AND platformversion=%(plat_version)s THEN 1 " \
                             "WHEN sourcepath = %(src_path)s AND lower(platformname)=%(plat_name)s THEN 2 " \
                             "WHEN lower(platformname)=%(plat_name)s AND platformversion=%(plat_version)s THEN 3 " \
                             "WHEN lower(platformname)=%(plat_name)s THEN 4 " \
                             "ELSE 5 " \
                             "END), updatedate DESC;"
    sql_filename_params = {'fname': file_name, 'src_path': source_path, 'plat_version': platform_version, 'plat_name': "android"}
    auto_id_comment = ""
    final_result_item = ""
    is_new = False

    # Match checksum and fileName
    df_result = get_list_by_using_query(sql_statement + sql_statement_checksum, sql_checksum_params, columns, conn, cur)
    if df_result is not None and len(df_result) > 0:  # Found a file with the same checksum.
        final_result_item = df_result
    else:  # Can't find files that have same name and checksum
        # Match tlsh and fileName
        df_result = get_list_by_using_query(sql_statement_filename, sql_filename_params, ['tlshchecksum'], conn, cur)
        if df_result is None or len(df_result) <= 0:
            final_result_item = ""
            auto_id_comment = "New Binary/"
            is_new = True
        elif tlsh_value == CONST_TLSH_NULL:  # Couldn't get the tlsh of a file.
            final_result_item = ""
        else:
            matched_tlsh = ""
            for row in df_result.tlshchecksum:
                try:
                    if row != CONST_TLSH_NULL:
                        tlsh_diff = tlsh.diff(row, tlsh_value)
                        if tlsh_diff <= 120:  # MATCHED
                            matched_tlsh = row
                            break
                except Exception as error:  # TLSH COMPARISON FAILED
                    logger.debug(f"Comparing TLSH:{error}")

            if matched_tlsh != "":
                final_result_item = get_list_by_using_query(
                    sql_statement + " WHERE filename=%(fname)s AND tlshchecksum=%(tlsh)s;", {'fname': file_name, 'tlsh': matched_tlsh},
                    columns, conn, cur)

    return final_result_item, auto_id_comment, is_new


def get_list_by_using_query(sql_query, params, columns, conn, cur):
    result_rows = ""  # DataFrame
    cur.execute(sql_query, params)
    rows = cur.fetchall()

    if rows is not None and len(rows) > 0:
        result_rows = pd.DataFrame(data=rows, columns=columns)
    return result_rows


def disconnect_lge_bin_db(conn, cur):
    # Close connection
    try:
        cur.close()
        conn.close()
    except Exception:
        pass
