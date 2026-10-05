#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import gzip
import zipfile

import pytest

from fosslight_android.android_binary_analysis import create_and_copy_notice_zip


@pytest.mark.run
@pytest.mark.release
def test_notice_zip_member_names_are_unique_after_path_flattening(tmp_path, monkeypatch):
    notice_files = [
        (tmp_path / "a_b" / "NOTICE.xml", b"plain flattened path"),
        (tmp_path / "a" / "b" / "NOTICE.xml", b"nested flattened path"),
        (tmp_path / "c_d" / "NOTICE.xml", b"plain notice"),
        (tmp_path / "c" / "d" / "NOTICE.xml.gz", b"compressed notice"),
    ]
    for notice_file, content in notice_files:
        notice_file.parent.mkdir(parents=True, exist_ok=True)
        if notice_file.suffix == ".gz":
            with gzip.open(notice_file, "wb") as output_file:
                output_file.write(content)
        else:
            notice_file.write_bytes(content)

    monkeypatch.chdir(tmp_path)
    zip_file = tmp_path / "notices.zip"
    create_and_copy_notice_zip([str(path) for path, _ in notice_files], str(zip_file))

    with zipfile.ZipFile(zip_file) as notice_zip:
        member_names = notice_zip.namelist()
        assert member_names == [
            "a_b_NOTICE.xml",
            "a_b_NOTICE_2.xml",
            "c_d_NOTICE.xml",
            "c_d_NOTICE_2.xml",
        ]
        assert len(member_names) == len(set(member_names))
        assert set(notice_zip.read(name) for name in member_names) == {
            content for _, content in notice_files
        }
