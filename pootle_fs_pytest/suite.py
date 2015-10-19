# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from fnmatch import fnmatch
import io
import os

from translate.storage.factory import getclass


def check_files_match(src, response):
    from pootle_fs.models import StoreFS

    assert all(
        os.path.exists(
            os.path.join(
                src,
                p.fs_path.strip("/")))
        for p
        in response["pushed_to_fs"])
    assert not any(
        os.path.exists(
            os.path.join(
                src,
                p.fs_path.strip("/")))
        for p
        in response["pruned_from_fs"])
    # Any Store/files that have been synced should now match
    synced = (
        response["pulled_to_pootle"]
        + response["pushed_to_fs"]
        + response["merged_from_fs"]
        + response["merged_from_pootle"]
        + response["merged_from_fs"])
    for action in synced:
        store_fs = StoreFS.objects.get(
            pootle_path=action.pootle_path)
        file_path = os.path.join(
            src,
            store_fs.path.strip("/"))
        store_f = io.BytesIO(store_fs.store.serialize())
        with open(file_path) as src_file:
            file_store = getclass(src_file)(src_file.read())
            serialized = getclass(store_f)(store_f.read())
            assert (
                [(x.source, x.target)
                 for x in file_store.units if x.source]
                == [(x.source, x.target)
                    for x in serialized.units if x.source])

    for action in response["removed"]:
        store = action.original_status.store_fs.store
        if store:
            assert store.obsolete is True
        assert action.original_status.store_fs.file.exists is False
        assert action.original_status.store_fs.pk is None
        assert not os.path.exists(
            os.path.join(src, action.fs_path.strip("/")))


def _check_fs(plugin, response):
    check_files_match(plugin.fs.url, response)


def _test_sync(plugin, **kwargs):
    from pootle_fs.models import FS_WINS, POOTLE_WINS

    status = plugin.status()
    pootle_path = kwargs.get("pootle_path", None)
    fs_path = kwargs.get("fs_path", None)

    check_fs = kwargs.get("check_fs", _check_fs)
    if "check_fs" in kwargs:
        del kwargs["check_fs"]

    expected = {}
    expected["pulled_to_pootle"] = []
    expected["pushed_to_fs"] = []
    expected["removed"] = []
    expected["merged_from_fs"] = []
    expected["merged_from_pootle"] = []

    response_mapping = {
        "merged_from_fs": ("merge_fs", ),
        "merged_from_pootle": ("merge_pootle", ),
        "pushed_to_fs": ("pootle_added", "pootle_ahead"),
        "pulled_to_pootle": ("fs_added", "fs_ahead"),
        "removed": ("to_remove", )}

    for expect, prev_status in response_mapping.items():
        _prev_status = []
        for k in prev_status:
            _prev_status += status[k]
        for fs_status in _prev_status:
            if pootle_path and not fnmatch(fs_status.pootle_path, pootle_path):
                continue
            if fs_path and not fnmatch(fs_status.fs_path, fs_path):
                continue
            expected[expect].append(fs_status)

    response = plugin.sync_translations(
        pootle_path=pootle_path, fs_path=fs_path)

    assert len(response) == len([k for k, v in expected.items() if v])

    for k, v in expected.items():
        assert len(response[k]) == len(expected[k])
        for i, item in enumerate(response[k]):
            expected_status = expected[k][i]
            original_status = item.original_status

            assert original_status.pootle_path == expected_status.pootle_path
            assert original_status.fs_path == expected_status.fs_path

            if k in ["pulled_to_pootle", "pushed_to_fs"]:
                assert item.store.pootle_path == expected_status.pootle_path
                assert item.store.fs.get().path == expected_status.fs_path
                store_fs = item.store.fs.get()
                assert (
                    store_fs.store.get_max_unit_revision()
                    == store_fs.last_sync_revision)
                assert (
                    store_fs.file.latest_hash
                    == store_fs.last_sync_hash)

    check_fs(plugin, response)

    # ensure there are no stale "staged_for_removal"
    # or "resolve_conflict" flags
    for store_fs in plugin.translations.filter(staged_for_removal=True):
        if pootle_path is not None:
            assert not fnmatch(store_fs.pootle_path, pootle_path)
        if fs_path is not None:
            assert not fnmatch(store_fs.path, fs_path)
        if pootle_path is None and fs_path is None:
            assert not store_fs
    resolved = plugin.translations.filter(
        resolve_conflict__in=[FS_WINS, POOTLE_WINS])
    for store_fs in resolved:
        if pootle_path is not None:
            assert not fnmatch(store_fs.pootle_path, pootle_path)
        if fs_path is not None:
            assert not fnmatch(store_fs.path, fs_path)
        if pootle_path is None and fs_path is None:
            assert not store_fs
    for store_fs in plugin.translations.filter(staged_for_merge=True):
        if pootle_path is not None:
            assert not fnmatch(store_fs.pootle_path, pootle_path)
        if fs_path is not None:
            assert not fnmatch(store_fs.path, fs_path)
        if pootle_path is None and fs_path is None:
            assert not store_fs


def _test_response(expected, response):

    assert (
        sorted(x for x in response)
        == sorted(k for k, v in expected.items() if v))

    for k, v in expected.items():
        assert len(response[k]) == len(expected[k])
        for i, item in enumerate(response[k]):
            # old_status = [x.pootle_path
            #               for x in new_status[expected[k][0].status]]
            expected_status = expected[k][i]
            original_status = response[k][i].original_status
            assert original_status.pootle_path == expected_status.pootle_path
            assert original_status.fs_path == expected_status.fs_path
            if original_status.store_fs:
                assert original_status.store_fs == expected_status.store_fs
            if original_status.store:
                assert original_status.store == expected_status.store


def _run_fetch_test(plugin, **kwargs):
    status = plugin.status()
    force = kwargs.get("force", None)
    pootle_path = kwargs.get("pootle_path", None)
    fs_path = kwargs.get("fs_path", None)
    expected = {}
    expected["fetched_from_fs"] = []
    to_fetch = status['fs_untracked']

    if force:
        to_fetch += (
            status["conflict_untracked"]
            + status["pootle_removed"]
            + status["conflict"])

    for fs_status in to_fetch:
        if pootle_path and not fnmatch(fs_status.pootle_path, pootle_path):
            continue
        if fs_path and not fnmatch(fs_status.fs_path, fs_path):
            continue
        expected["fetched_from_fs"].append(fs_status)
    response = plugin.fetch_translations(
        pootle_path=pootle_path, fs_path=fs_path, force=force)
    _test_response(expected, response)
    _test_sync(plugin, **kwargs)


def _run_add_test(plugin, **kwargs):
    status = plugin.status()
    force = kwargs.get("force", None)
    pootle_path = kwargs.get("pootle_path", None)
    fs_path = kwargs.get("fs_path", None)
    expected = {}
    expected["added_from_pootle"] = []
    to_add = status['pootle_untracked']
    if force:
        to_add += (
            status["conflict_untracked"]
            + status["fs_removed"]
            + status["conflict"])
    for fs_status in to_add:
        if pootle_path and not fnmatch(fs_status.pootle_path, pootle_path):
            continue
        if fs_path and not fnmatch(fs_status.fs_path, fs_path):
            continue
        expected["added_from_pootle"].append(fs_status)
    response = plugin.add_translations(
        pootle_path=pootle_path, fs_path=fs_path, force=force)
    _test_response(expected, response)
    _test_sync(plugin, **kwargs)


def _run_rm_test(plugin, **kwargs):
    status = plugin.status()
    pootle_path = kwargs.get("pootle_path", None)
    fs_path = kwargs.get("fs_path", None)
    expected = {}
    expected["staged_for_removal"] = []
    to_remove = (
        status["fs_untracked"] + status["pootle_untracked"]
        + status["conflict_untracked"]
        + status["pootle_removed"] + status["fs_removed"])
    for fs_status in to_remove:
        if pootle_path and not fnmatch(fs_status.pootle_path, pootle_path):
            continue
        if fs_path and not fnmatch(fs_status.fs_path, fs_path):
            continue
        expected["staged_for_removal"].append(fs_status)
    response = plugin.rm_translations(
        pootle_path=pootle_path, fs_path=fs_path)
    _test_response(expected, response)
    _test_sync(plugin, **kwargs)


def _run_merge_test(plugin, **kwargs):
    status = plugin.status()
    pootle_path = kwargs.get("pootle_path", None)
    fs_path = kwargs.get("fs_path", None)
    pootle_wins = kwargs.get("pootle_wins", False)
    action_type = "staged_for_merge_fs"
    if pootle_wins:
        action_type = "staged_for_merge_pootle"
    expected = {}
    expected[action_type] = []
    to_remove = (
        status["conflict_untracked"] + status["conflict"])
    for fs_status in to_remove:
        if pootle_path and not fnmatch(fs_status.pootle_path, pootle_path):
            continue
        if fs_path and not fnmatch(fs_status.fs_path, fs_path):
            continue
        expected[action_type].append(fs_status)
    response = plugin.merge_translations(
        pootle_path=pootle_path, fs_path=fs_path, pootle_wins=pootle_wins)
    _test_response(expected, response)
    _test_sync(plugin, **kwargs)


def run_fetch_test(plugin, **kwargs):
    _run_fetch_test(plugin, force=False, **kwargs)
    _run_fetch_test(plugin, force=True, **kwargs)


def run_add_test(plugin, **kwargs):
    _run_add_test(plugin, force=False, **kwargs)
    _run_add_test(plugin, force=True, **kwargs)


def run_rm_test(plugin, **kwargs):
    _run_rm_test(plugin, **kwargs)


def run_merge_test(plugin, **kwargs):
    _run_merge_test(plugin, **kwargs)
