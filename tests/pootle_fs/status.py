#!/usr/bin/env python
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
from pootle_fs.status import ProjectFSStatus

from ..fixtures.pootle_fs_fixtures import (
    STATUS_TYPES, _test_status, _edit_file)


@pytest.mark.django
def test_status(fs_plugin, english, zulu, expected_fs_stores):
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
    assert sorted(status['fs_untracked']) == sorted(expected_fs_stores)

    # when we fetch the translations their status is set to fs_added
    fs_plugin.fetch_translations()
    status = fs_plugin.status()
    assert "fs_added" in status
    assert len(status["fs_added"]) == len(expected_fs_stores)
    assert all([isinstance(x, StoreFS) for x in status['fs_added']])

    # pulling the translations makes us up-to-date
    fs_plugin.pull_translations()
    status = fs_plugin.status()
    assert status.has_changed is False


@pytest.mark.django
def test_status_check_status(fs_plugin_fs_untracked, system):
    plugin = fs_plugin_fs_untracked
    plugin.fetch_translations()
    plugin.pull_translations()
    status = plugin.status()
    assert status.has_changed is False
    _edit_file(plugin, "po/en.po")
    status.check_status()
    assert status.has_changed is True


@pytest.mark.django
def test_statuses(fs_status):
    plugin, cb, outcome = fs_status
    cb(plugin)
    if outcome:
        for k, v in outcome.items():
            if k in ["fs_untracked", "conflict_untracked"]:
                continue
            if k == "pootle_untracked":
                outcome[k] = [
                    (Store.objects.get(pootle_path=pp), p)
                    for pp, p in v]
            else:
                outcome[k] = [
                    StoreFS.objects.get(
                        pootle_path=pp, path=p)
                    for pp, p in v]
    _test_status(plugin, outcome)
