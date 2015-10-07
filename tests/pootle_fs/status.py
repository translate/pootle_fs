#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_fs.models import StoreFS
from pootle_fs.status import ProjectFSStatus

from pootle_fs_pytest.utils import (
    STATUS_TYPES, _test_status, _edit_file)


@pytest.mark.django
def test_status_instance(fs_plugin, english, zulu, expected_fs_stores):
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
    assert (
        sorted(expected_fs_stores) == sorted(
            [(s.pootle_path, s.fs_path)
             for s in status['fs_untracked']]))

    # when we fetch the translations their status is set to fs_added
    fs_plugin.fetch_translations()
    status = fs_plugin.status()
    assert "fs_added" in status
    assert len(status["fs_added"]) == len(expected_fs_stores)
    assert all([isinstance(x.store_fs, StoreFS) for x in status['fs_added']])

    # pulling the translations makes us up-to-date
    fs_plugin.pull_translations()
    status = fs_plugin.status()
    assert status.has_changed is False

    # We can reload the status object with status.check_status()
    _edit_file(fs_plugin, "gnu_style/po/en.po")
    assert status.has_changed is False
    status.check_status()
    assert status.has_changed is True


# Parametrized: PLUGIN_STATUS
@pytest.mark.django
def test_status(fs_status):
    plugin, cb, outcome = fs_status
    cb(plugin)
    _test_status(plugin, outcome)
