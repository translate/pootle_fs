from fnmatch import fnmatch
import os

import pytest

from pootle_store.models import Store


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
    response = plugin.fetch_translations(**kwargs)
    # new_status = plugin.status()

    assert (
        sorted(x for x in response)
        == sorted(k for k, v in expected.items() if v))

    for k, v in expected.items():
        assert len(response[k]) == len(expected[k])
        for i, item in enumerate(response[k]):
            # old_status = [x.pootle_path
            #               for x in new_status[expected[k][0].status]]
            assert response[k][i].original_status == expected[k][i]


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
    response = plugin.add_translations(**kwargs)
    # new_status = plugin.status()

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


def _check_fs(plugin, response):
    pushed = [
        os.path.join(plugin.fs.url, p.fs_path.strip("/"))
        for p in response["pushed_to_fs"]]
    pruned = [
        os.path.join(plugin.fs.url, p.fs_path.strip("/"))
        for p in response["pruned_from_fs"]]

    for p in pushed:
        assert os.path.exists(p)

    for p in pruned:
        assert not os.path.exists(p)


def _run_push_test(plugin, **kwargs):
    status = plugin.status()
    force = kwargs.get("force", None)
    pootle_path = kwargs.get("pootle_path", None)
    fs_path = kwargs.get("fs_path", None)
    prune = kwargs.get("prune", False)
    if "prune" in kwargs:
        del kwargs["prune"]
    force = kwargs.get("force", False)
    if "force" in kwargs:
        del kwargs["force"]
    check_fs = kwargs.get("check_fs", _check_fs)
    if "check_fs" in kwargs:
        del kwargs["check_fs"]

    expected = {}
    expected["pushed_to_fs"] = []
    expected["pruned_from_fs"] = []

    to_push = status["pootle_untracked"] + status["pootle_ahead"]

    if force:
        to_push += (
            status["conflict"]
            + status["conflict_untracked"]
            + status["fs_removed"])

    for fs_status in to_push:
        if pootle_path and not fnmatch(fs_status.pootle_path, pootle_path):
            continue
        if fs_path and not fnmatch(fs_status.fs_path, fs_path):
            continue
        expected["pushed_to_fs"].append(fs_status)

    if prune:
        to_prune = (
            status["pootle_removed"]
            + status["fs_untracked"])
        for fs_status in to_prune:
            if pootle_path and not fnmatch(fs_status.pootle_path, pootle_path):
                continue
            if fs_path and not fnmatch(fs_status.fs_path, fs_path):
                continue
            expected["pruned_from_fs"].append(fs_status)

    plugin.add_translations(force=force, **kwargs)
    response = plugin.push_translations(prune=prune, **kwargs)

    assert len(response) == len([k for k, v in expected.items() if v])

    for k, v in expected.items():
        assert len(response[k]) == len(expected[k])
        for i, item in enumerate(response[k]):
            expected_status = expected[k][i]
            original_status = item.original_status

            assert original_status.pootle_path == expected_status.pootle_path
            assert original_status.fs_path == expected_status.fs_path

            if k == "pruned_from_fs":
                if original_status in status['fs_untracked']:
                    file_path = os.path.join(
                        plugin.local_fs_path,
                        original_status.fs_path.strip("/"))
                    assert not os.path.exists(file_path)
                else:
                    assert original_status.store_fs.file.exists is False
                    assert original_status.store_fs.pk is None
            elif k == "pushed_to_fs":
                store_fs = item.store.fs.get()
                assert (
                    store_fs.store.get_max_unit_revision()
                    == store_fs.last_sync_revision)
                assert (
                    store_fs.file.latest_hash
                    == store_fs.last_sync_hash)

    check_fs(plugin, response)


def _run_pull_test(plugin, **kwargs):
    status = plugin.status()
    force = kwargs.get("force", None)
    pootle_path = kwargs.get("pootle_path", None)
    fs_path = kwargs.get("fs_path", None)
    prune = kwargs.get("prune", False)
    if "prune" in kwargs:
        del kwargs["prune"]
    force = kwargs.get("force", False)
    if "force" in kwargs:
        del kwargs["force"]

    expected = {}
    expected["pulled_to_pootle"] = []
    expected["pruned_from_pootle"] = []

    to_pull = status["fs_untracked"] + status["fs_ahead"]

    if force:
        to_pull += (
            status["conflict"]
            + status["conflict_untracked"]
            + status["pootle_removed"])

    for fs_status in to_pull:
        if pootle_path and not fnmatch(fs_status.pootle_path, pootle_path):
            continue
        if fs_path and not fnmatch(fs_status.fs_path, fs_path):
            continue
        expected["pulled_to_pootle"].append(fs_status)

    if prune:
        to_prune = (
            status["fs_removed"]
            + status["pootle_untracked"])
        for fs_status in to_prune:
            if pootle_path and not fnmatch(fs_status.pootle_path, pootle_path):
                continue
            if fs_path and not fnmatch(fs_status.fs_path, fs_path):
                continue
            expected["pruned_from_pootle"].append(fs_status)

    plugin.fetch_translations(force=force, **kwargs)
    response = plugin.pull_translations(prune=prune, **kwargs)

    assert len(response) == len([k for k, v in expected.items() if v])

    for k, v in expected.items():
        assert len(response[k]) == len(expected[k])

        for i, item in enumerate(response[k]):
            expected_status = expected[k][i]
            original_status = item.original_status

            assert original_status.pootle_path == expected_status.pootle_path
            assert original_status.fs_path == expected_status.fs_path

            if k == "pruned_from_pootle":
                with pytest.raises(Store.DoesNotExist):
                    Store.objects.get(pootle_path=item.pootle_path)

            elif k == "pushed_to_pootle":
                assert item.store.pootle_path == expected_status.pootle_path
                assert item.store.fs.get().path == expected_status.fs_path
                store_fs = item.store.fs.get()
                assert (
                    store_fs.store.get_max_unit_revision()
                    == store_fs.last_sync_revision)
                assert (
                    store_fs.file.latest_hash
                    == store_fs.last_sync_hash)


def run_fetch_test(plugin, **kwargs):
    _run_fetch_test(plugin, force=False, **kwargs)
    _run_fetch_test(plugin, force=True, **kwargs)


def run_add_test(plugin, **kwargs):
    _run_add_test(plugin, force=False, **kwargs)
    _run_add_test(plugin, force=True, **kwargs)


def run_pull_test(plugin, **kwargs):
    _run_pull_test(plugin, force=False, prune=False, **kwargs)
    _run_pull_test(plugin, force=False, prune=True, **kwargs)
    _run_pull_test(plugin, force=True, prune=False, **kwargs)
    _run_pull_test(plugin, force=True, prune=True, **kwargs)


def run_push_test(plugin, **kwargs):
    _run_push_test(plugin, force=False, prune=False, **kwargs)
    _run_push_test(plugin, force=False, prune=True, **kwargs)
    _run_push_test(plugin, force=True, prune=False, **kwargs)
    _run_push_test(plugin, force=True, prune=True, **kwargs)
