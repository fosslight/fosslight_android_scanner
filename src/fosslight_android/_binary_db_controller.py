#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Binary DB lookup via ldb_service POST /binary/match."""
import json
import logging
import os
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

from ._common import CONST_TLSH_NULL
from fosslight_util.constant import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

DEFAULT_KB_URL = "http://fosslight-kb.lge.com/"
_BINARY_MATCH_PATH = "/binary/match"
_HTTP_TIMEOUT_SEC = 120
_CHUNK_SIZE = int(os.environ.get("BINARY_MATCH_CHUNK_SIZE", "3000"))

MatchKey = Tuple[str, str]


def resolve_kb_config(kb_url: str = "", kb_token: str = "") -> Tuple[str, str]:
    url = (kb_url or os.environ.get("KB_URL", DEFAULT_KB_URL)).strip() or DEFAULT_KB_URL
    token = (kb_token or "").strip() or (os.environ.get("KB_TOKEN") or "").strip()
    return f"{url.rstrip('/')}/", token


def _item_filename(item) -> str:
    return item.binary_name_without_path or os.path.basename(item.bin_name)


def _match_key(filename: str, checksum: str) -> MatchKey:
    return filename, checksum or ""


def _build_deduped_payload(bin_info_list) -> Tuple[List[dict], Dict[MatchKey, str]]:
    """Deduplicate by filename+checksum; return API payload and key→api_id map."""
    key_to_id: Dict[MatchKey, str] = {}
    items_payload: List[dict] = []

    for item in bin_info_list:
        filename = _item_filename(item)
        checksum = item.checksum or ""
        key = _match_key(filename, checksum)
        if key in key_to_id:
            continue
        api_id = str(len(items_payload))
        key_to_id[key] = api_id
        items_payload.append({
            "id": api_id,
            "filename": filename,
            "checksum": checksum,
            "tlsh": item.tlsh or CONST_TLSH_NULL,
        })

    return items_payload, key_to_id


def _apply_match_result_to_item(item, result: Optional[dict]) -> None:
    if not result or not result.get("matched"):
        item.set_comment("New Binary/")
        item.is_new_bin = True
        return

    oss_rows = result.get("oss_items") or []
    if not oss_rows:
        item.set_comment("New Binary/")
        item.is_new_bin = True
        return

    item.is_new_bin = False
    item.set_comment("")
    for row_idx, row in enumerate(oss_rows):
        if row_idx == 0:
            item.set_oss_name(row.get("oss_name") or "")
            item.set_oss_version(row.get("oss_version") or "")
            item.set_license(row.get("license") or "")
        else:
            item.set_additional_oss_items(
                f"{row.get('oss_name') or ''}\t"
                f"{row.get('oss_version') or ''}\t"
                f"{row.get('license') or ''}"
            )


def get_oss_info_from_db(bin_info_list, kb_url: str = "", kb_token: str = ""):
    """
    Call ldb_service /binary/match and apply OSS info.
    Deduplicates by filename+checksum before the API call and maps results back.
    """
    if not bin_info_list:
        return bin_info_list

    base_url, token = resolve_kb_config(kb_url, kb_token)
    items_payload, key_to_id = _build_deduped_payload(bin_info_list)
    if not items_payload:
        return bin_info_list

    results_by_id = {}
    try:
        for chunk_start in range(0, len(items_payload), _CHUNK_SIZE):
            chunk = items_payload[chunk_start: chunk_start + _CHUNK_SIZE]
            response = _post_binary_match(base_url, token, chunk)
            if response is None:
                return bin_info_list
            for result in response.get("results", []):
                results_by_id[str(result.get("id"))] = result
    except Exception as error:
        logger.warning(f"Binary match API failed: {error}")
        return bin_info_list

    for item in bin_info_list:
        try:
            key = _match_key(_item_filename(item), item.checksum or "")
            api_id = key_to_id.get(key)
            if api_id is None:
                continue
            _apply_match_result_to_item(item, results_by_id.get(api_id))
        except Exception as error:
            logger.warning(f"READ OSS :{error}")

    return bin_info_list


def _post_binary_match(kb_url: str, kb_token: str, items: list) -> Optional[dict]:
    data = json.dumps({"items": items}).encode("utf-8")
    request = urllib.request.Request(
        f"{kb_url.rstrip('/')}{_BINARY_MATCH_PATH}",
        data=data,
        method="POST",
    )
    request.add_header("Accept", "application/json")
    request.add_header("Content-Type", "application/json")
    if kb_token:
        request.add_header("Authorization", f"Bearer {kb_token}")

    try:
        with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT_SEC) as response:
            body = response.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as ex:
        body = ""
        try:
            body = ex.read().decode()
        except Exception:
            pass
        logger.warning(f"Binary match HTTP {ex.code}: {body or ex.reason}")
        return None
    except urllib.error.URLError as ex:
        logger.debug(f"Binary match unreachable: {ex}")
        return None
