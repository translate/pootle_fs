# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_store.models import Store

from pootle_fs.response import FS_ACTION, ActionResponse, ActionStatus
from pootle_fs.status import Status
from pootle_fs.models import StoreFS


def _test_response(response):
    assert isinstance(response, ActionResponse)

    for k in response:
        assert all(
            isinstance(a, ActionStatus)
            for a in response[k])
        assert all(
            isinstance(a.store_fs, StoreFS)
            for a in response[k]
            if a.store_fs)
        assert all(
            isinstance(a.store, Store)
            for a in response[k]
            if a.store)
        assert all(
            isinstance(a.original_status, Status)
            for a in response[k])
        for action in response[k]:
            assert (
                str(action)
                == ("<FSAction(%s): %s %s::%s>"
                    % (action.project, action.action_type,
                       action.pootle_path, action.fs_path)))
            assert action.action_type == k
            assert action.complete is True
            assert action.failed is False
            assert action.plugin == action.original_status.plugin
            assert action.project == action.original_status.project
            assert action.original_status.store_fs == action.store_fs
            if action.original_status.store:
                assert action.original_status.store == action.store
            assert action.original_status.pootle_path == action.pootle_path
            assert action.original_status.fs_path == action.fs_path


@pytest.mark.django
def test_response_action_add_fetch(fs_plugin_suite):
    plugin = fs_plugin_suite
    plugin.status()
    _test_response(plugin.sync_translations())
    _test_response(plugin.add_translations())
    _test_response(plugin.sync_translations())
    _test_response(plugin.fetch_translations())
    _test_response(plugin.sync_translations())


@pytest.mark.django
def test_response_action_rm(fs_plugin_suite):
    plugin = fs_plugin_suite
    plugin.status()
    _test_response(plugin.rm_translations())
    _test_response(plugin.sync_translations())


@pytest.mark.django
def test_response_action_merge(fs_plugin_suite):
    plugin = fs_plugin_suite
    plugin.status()
    _test_response(plugin.merge_translations())
    _test_response(plugin.sync_translations())


@pytest.mark.django
def test_response_action_merge_pootle(fs_plugin_suite):
    plugin = fs_plugin_suite
    plugin.status()
    _test_response(plugin.merge_translations(pootle_wins=True))
    _test_response(plugin.sync_translations())


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


@pytest.mark.django
def test_response_arg(fs_plugin_suite):
    plugin = fs_plugin_suite
    plugin.status()
    response = ActionResponse(plugin)
    new_response = plugin.merge_translations(response=response)
    assert response is new_response

    new_response = plugin.add_translations(response=response)
    assert response is new_response

    new_response = plugin.pull_translations(response=response)
    assert response is new_response

    new_response = plugin.push_translations(response=response)
    assert response is new_response

    new_response = plugin.rm_translations(response=response)
    assert response is new_response

    new_response = plugin.sync_translations(response=response)
    assert response is new_response
