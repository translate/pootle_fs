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
from pootle_fs.status import ProjectFSStatus, ActionResponse, FS_ACTION

from pootle_fs_pytest.utils import (
    STATUS_TYPES, _test_status, _edit_file)


@pytest.mark.django
def test_status_instance(fs_plugin):
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

    # when we fetch the translations their status is set to fs_added
    fs_plugin.fetch_translations()
    status = fs_plugin.status()
    assert "fs_added" in status
    assert all([isinstance(x.store_fs, StoreFS) for x in status['fs_added']])

    # pulling the translations makes us up-to-date
    fs_plugin.pull_translations()
    status = fs_plugin.status()
    assert status.has_changed is False

    # We can reload the status object with status.check_status()
    old_status = fs_plugin.status()
    _edit_file(fs_plugin, "/gnu_style/po/en.po")
    assert old_status.has_changed is False
    assert status.has_changed is False

    new_status = status.check_status()

    assert old_status.has_changed is False
    assert status.has_changed is True
    assert new_status.has_changed is True


# Parametrized: PLUGIN_STATUS
@pytest.mark.django
def test_status(fs_status):
    plugin, cb, outcome = fs_status
    cb(plugin)
    _test_status(plugin, outcome)


@pytest.mark.django
def test_action_response(fs_plugin):
    response = ActionResponse(fs_plugin)
    assert [x for x in response] == []
    assert response.action_types == FS_ACTION.keys()
    for action_type in response.action_types:
        assert response[action_type] == []

    assert list(response.completed()) == []
    for action_type in response.action_types:
        assert list(response.completed(action_type)) == []
    assert list(response.completed(*response.action_types)) == []

    assert list(response.failed()) == []
    for action_type in response.action_types:
        assert list(response.failed(action_type)) == []
    assert list(response.failed(*response.action_types)) == []
    assert not response.has_failed


@pytest.mark.django
def test_action_response_success(fs_plugin):
    response = ActionResponse(fs_plugin)
    status = fs_plugin.status()

    for fs_status in status["fs_untracked"]:
        action = response.add("fetched_from_fs", fs_status)
        assert action.original_status == fs_status
        assert action.failed is False
        assert action.complete is True

    assert len(list(response.completed())) == 18
    assert (
        len(list(response.completed("fetched_from_fs")))
        == 18)
    assert (
        len(list(response.completed("fetched_from_fs", "added_from_pootle")))
        == 18)
    assert list(response.failed()) == []
    assert not response.has_failed


@pytest.mark.django
def test_action_response_failure(fs_plugin):
    response = ActionResponse(fs_plugin)
    status = fs_plugin.status()

    for fs_status in status["fs_untracked"]:
        action = response.add("fetched_from_fs", fs_status, complete=False)
        assert action.original_status == fs_status
        assert action.failed is True
        assert action.complete is False

    assert len(list(response.failed())) == 18
    assert len(list(response.failed("fetched_from_fs"))) == 18
    assert (
        len(list(response.failed("fetched_from_fs", "added_from_pootle")))
        == 18)
    assert list(response.completed()) == []
    assert response.has_failed


@pytest.mark.django
def test_action_response_on_success(fs_plugin):
    response = ActionResponse(fs_plugin)
    status = fs_plugin.status()

    for fs_status in status["fs_untracked"]:
        action = response.add("fetched_from_fs", fs_status, complete=False)

    for action in response.failed():
        action.complete = True

    assert len(list(response.completed())) == 18
    assert len(list(response.completed("fetched_from_fs"))) == 18
    assert (
        len(list(response.completed("fetched_from_fs", "added_from_pootle")))
        == 18)
    assert list(response.failed()) == []
    assert not response.has_failed
