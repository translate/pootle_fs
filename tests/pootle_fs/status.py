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
    STATUS_TYPES, _test_status,
    _edit_file, _remove_file, _remove_store, _update_store)


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
def test_status_add_fs_not_matching(fs_plugin, english,
                                    zulu, expected_fs_stores):
    fs_plugin.fetch_translations()
    fs_plugin.pull_translations()
    status = fs_plugin.status()
    assert status.has_changed is False
    _edit_file(fs_plugin, "foo.po")
    fs_plugin.fetch_translations()
    status = fs_plugin.status()
    assert status.has_changed is False


@pytest.mark.django
def test_status_conflict_untracked(fs_plugin_conflict_untracked):
    _test_status(
        fs_plugin_conflict_untracked,
        dict(conflict_untracked=[(u'/en/tutorial/en.po', '/po/en.po')]))


@pytest.mark.django
def test_status_fs_untracked(fs_plugin_fs_untracked):
    _test_status(
        fs_plugin_fs_untracked,
        dict(fs_untracked=[(u'/en/tutorial/en.po', '/po/en.po')]))


@pytest.mark.django
def test_status_pootle_untracked(fs_plugin_pootle_untracked):
    _test_status(
        fs_plugin_pootle_untracked,
        dict(pootle_untracked=[
                (Store.objects.get(pootle_path=u'/en/tutorial/en.po'),
                 '/po/en.po')]))


@pytest.mark.django
def test_status_fs_added(fs_plugin_fs_untracked):
    plugin = fs_plugin_fs_untracked
    plugin.fetch_translations()
    _test_status(
        plugin,
        dict(
            fs_added=[
                StoreFS.objects.get(
                    pootle_path=u'/en/tutorial/en.po',
                    path='/po/en.po')]))


@pytest.mark.django
def test_status_pootle_added(fs_plugin_pootle_untracked):
    plugin = fs_plugin_pootle_untracked
    plugin.add_translations()
    _test_status(
        plugin,
        dict(
            pootle_added=[
                StoreFS.objects.get(
                    pootle_path=u'/en/tutorial/en.po',
                    path='/po/en.po')]))


@pytest.mark.django
def test_status_pootle_ahead(fs_plugin_pootle_untracked, system):
    plugin = fs_plugin_pootle_untracked
    plugin.add_translations()
    plugin.push_translations()
    _update_store(plugin)
    print plugin.status()
    _test_status(
        plugin,
        dict(
            pootle_ahead=[
                StoreFS.objects.get(
                    pootle_path=u'/en/tutorial/en.po',
                    path='/po/en.po')]))


@pytest.mark.django
def test_status_fs_ahead(fs_plugin_fs_untracked):
    plugin = fs_plugin_fs_untracked
    plugin.fetch_translations()
    plugin.pull_translations()
    _edit_file(plugin, "po/en.po")
    _test_status(
        plugin,
        dict(
            fs_ahead=[
                StoreFS.objects.get(
                    pootle_path=u'/en/tutorial/en.po',
                    path='/po/en.po')]))


@pytest.mark.django
def test_status_fs_removed(fs_plugin_fs_untracked):
    plugin = fs_plugin_fs_untracked
    plugin.fetch_translations()
    plugin.pull_translations()
    _remove_file(plugin, "po/en.po")
    _test_status(
        plugin,
        dict(
            fs_removed=[
                StoreFS.objects.get(
                    pootle_path=u'/en/tutorial/en.po',
                    path='/po/en.po')]))


@pytest.mark.django
def test_status_pootle_removed(fs_plugin_pootle_untracked):
    plugin = fs_plugin_pootle_untracked
    plugin.add_translations()
    plugin.push_translations()
    _remove_store(plugin)
    _test_status(
        plugin,
        dict(
            pootle_removed=[
                StoreFS.objects.get(
                    pootle_path=u'/en/tutorial/en.po',
                    path='/po/en.po')]))


@pytest.mark.django
def test_status_conflict(fs_plugin_fs_untracked, system):
    plugin = fs_plugin_fs_untracked
    plugin.fetch_translations()
    plugin.pull_translations()
    _edit_file(plugin, "po/en.po")
    _update_store(plugin)
    _test_status(
        plugin,
        dict(
            conflict=[
                StoreFS.objects.get(
                    pootle_path=u'/en/tutorial/en.po',
                    path='/po/en.po')]))


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
