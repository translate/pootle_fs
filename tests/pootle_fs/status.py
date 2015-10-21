# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_store.models import Store

from pootle_fs.models import StoreFS
from pootle_fs.status import ProjectFSStatus, Status

from pootle_fs_pytest.utils import (
    STATUS_TYPES, _test_status, _edit_file)


@pytest.mark.django
def test_project_status_instance(fs_plugin):
    assert fs_plugin.is_cloned is False
    status = fs_plugin.status()

    # calling status will call pull
    assert fs_plugin.is_cloned is True
    assert isinstance(status, ProjectFSStatus)
    assert str(status) == (
        "<ProjectFSStatus(Tutorial): fs_untracked: 18>")
    assert status.has_changed is True
    for k in STATUS_TYPES:
        if k == "fs_untracked":
            continue
        assert status[k] == []
        assert k not in status

    assert not status.get_unchanged()

    # when we fetch the translations their status is set to fs_added
    fs_plugin.fetch_translations()
    status = fs_plugin.status()
    assert "fs_added" in status
    assert all([isinstance(x.store_fs, StoreFS) for x in status['fs_added']])

    # pulling the translations makes us up-to-date
    fs_plugin.pull_translations()
    status = fs_plugin.status()
    assert status.has_changed is False
    assert str(status) == "<ProjectFSStatus(Tutorial): Everything up-to-date>"

    unchanged = status.get_unchanged()
    assert StoreFS.objects.count() == len(unchanged)
    for status_fs in unchanged:
        assert isinstance(status_fs, StoreFS)

    # We can reload the status object with status.check_status()
    old_status = fs_plugin.status()
    _edit_file(fs_plugin, "/gnu_style/po/en.po")
    assert old_status.has_changed is False
    assert status.has_changed is False

    new_status = status.check_status()

    assert old_status.has_changed is False
    assert status.has_changed is True
    assert new_status.has_changed is True


@pytest.mark.django
def test_status_ordering(fs_plugin_suite):
    plugin = fs_plugin_suite
    status = plugin.status()
    all_status = []
    for k in status:
        all_status += status[k]

    # status objects are inherently ordered by pootle_path
    assert (
        [s.pootle_path for s in sorted(all_status)]
        == sorted(s.pootle_path for s in all_status))

    # status objects are equal if they have same data
    new_status = plugin.status()

    for k in status:
        for i, status_fs in enumerate(status[k]):
            assert new_status[k][i] == status_fs
            assert new_status[k][i] is not status_fs
            assert status_fs > 0


@pytest.mark.django
def test_status_instance(fs_plugin_suite):
    plugin = fs_plugin_suite

    status = plugin.status()

    with pytest.raises(TypeError):
        Status()

    with pytest.raises(ValueError):
        Status(status)

    with pytest.raises(ValueError):
        Status(status, pootle_path="/foo")

    with pytest.raises(ValueError):
        Status(status, fs_path="/bar")

    with pytest.raises(ValueError):
        Status(status, store=Store.objects.first())

    # We can manually set the pootle/fs_paths
    Status(status, pootle_path="/foo", fs_path="/bar")

    # Or we can pass a store_fs
    Status(status, store_fs=StoreFS.objects.first())

    # Or we can pass a store and fs_path
    Status(status, store=Store.objects.first(), fs_path="/bar")

    # Pootle path is ignored in this case
    store_fs = Store.objects.first()
    fs_status = Status(
        status, store=store_fs,
        pootle_path="/foo", fs_path="/bar")
    assert fs_status.pootle_path == store_fs.pootle_path
    assert fs_status.pootle_path != "/foo"

    # If we use a store_fs that overrides everything
    store_fs = StoreFS.objects.last()
    store = Store.objects.first()
    assert store_fs.store != store
    fs_status = Status(
        status, store_fs=store_fs, store=store,
        pootle_path="/foo", fs_path="/bar")
    assert fs_status.pootle_path == store_fs.pootle_path
    assert fs_status.fs_path == store_fs.path
    assert fs_status.store == store_fs.store


# Parametrized: PLUGIN_STATUS
@pytest.mark.django
def test_status(fs_status):
    plugin, cb, outcome = fs_status
    cb(plugin)
    _test_status(plugin, outcome)
