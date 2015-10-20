#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_fs.response import FS_ACTION, ActionResponse


@pytest.mark.django
def test_response_instance(fs_plugin):
    plugin = fs_plugin
    plugin.status()
    response = plugin.sync_translations()
    assert isinstance(response, ActionResponse)
    assert str(response) == (
        "<FSActionResponse(Tutorial): No changes made>")
    assert response.has_failed is False
    assert response.made_changes is False
    assert "fetched_from_fs" not in response
    assert response["fetched_from_fs"] == []
    response = plugin.fetch_translations(pootle_path="/en*")
    assert str(response) == (
        "<FSActionResponse(Tutorial): fetched_from_fs: 9>")
    assert "fetched_from_fs" in response
    assert len(response["fetched_from_fs"]) == 9
    assert response.has_failed is False

    response = plugin.rm_translations()
    assert str(response) == (
        "<FSActionResponse(Tutorial): staged_for_removal: 9>")
    assert "fetched_from_fs" not in response
    assert "staged_for_removal" in response
    assert len(response["staged_for_removal"]) == 9
    assert response.has_failed is False

    response = plugin.sync_translations()
    assert str(response) == (
        "<FSActionResponse(Tutorial): pulled_to_pootle: 9, removed: 9>")
    assert "pulled_to_pootle" in response
    assert "removed" in response
    assert len(response["pulled_to_pootle"]) == 9
    assert len(response["removed"]) == 9
    assert response.has_failed is False


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
