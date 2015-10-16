from fnmatch import fnmatch
import os


def _check_fs(plugin, response):
    from pootle_fs.models import StoreFS

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

    for response in response["pushed_to_fs"]:
        store_fs = StoreFS.objects.get(
            pootle_path=response.pootle_path)
        serialized = store_fs.store.serialize()
        assert serialized == store_fs.file.read()


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

    for fs_status in (status["merge_fs"]):
        if pootle_path and not fnmatch(fs_status.pootle_path, pootle_path):
            continue
        if fs_path and not fnmatch(fs_status.fs_path, fs_path):
            continue
        expected["merged_from_fs"].append(fs_status)

    for fs_status in (status["merge_pootle"]):
        if pootle_path and not fnmatch(fs_status.pootle_path, pootle_path):
            continue
        if fs_path and not fnmatch(fs_status.fs_path, fs_path):
            continue
        expected["merged_from_pootle"].append(fs_status)

    for fs_status in (status["pootle_added"] + status["pootle_ahead"]):
        if pootle_path and not fnmatch(fs_status.pootle_path, pootle_path):
            continue
        if fs_path and not fnmatch(fs_status.fs_path, fs_path):
            continue
        expected["pushed_to_fs"].append(fs_status)

    for fs_status in (status["fs_added"] + status["fs_ahead"]):
        if pootle_path and not fnmatch(fs_status.pootle_path, pootle_path):
            continue
        if fs_path and not fnmatch(fs_status.fs_path, fs_path):
            continue
        expected["pulled_to_pootle"].append(fs_status)

    for fs_status in status["to_remove"]:
        if pootle_path and not fnmatch(fs_status.pootle_path, pootle_path):
            continue
        if fs_path and not fnmatch(fs_status.fs_path, fs_path):
            continue
        expected["removed"].append(fs_status)

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

            elif k == "to_remove":
                if original_status in status['fs_untracked']:
                    file_path = os.path.join(
                        plugin.local_fs_path,
                        original_status.fs_path.strip("/"))
                    assert not os.path.exists(file_path)
                else:
                    assert original_status.store_fs.file.exists is False
                    assert original_status.store_fs.pk is None

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
    response = plugin.rm_translations(**kwargs)
    _test_response(expected, response)
    _test_sync(plugin, **kwargs)


def _run_merge_test(plugin, **kwargs):
    status = plugin.status()
    pootle_path = kwargs.get("pootle_path", None)
    fs_path = kwargs.get("fs_path", None)
    action_type = "staged_for_merge_fs"
    if kwargs.get("pootle_wins", False):
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
    response = plugin.merge_translations(**kwargs)
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
