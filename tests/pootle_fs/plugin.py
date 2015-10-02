#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest
from ConfigParser import ConfigParser

from pootle_store.models import Store

from pootle_fs.models import StoreFS

from ..fixtures.pootle_fs_fixtures import (
    _test_status, _edit_file, _update_store, _setup_store)


@pytest.mark.django
def test_plugin_instance(fs_plugin):
    assert fs_plugin.project == fs_plugin.fs.project
    assert fs_plugin.local_fs_path.endswith(fs_plugin.project.code)
    assert fs_plugin.is_cloned is False
    assert fs_plugin.stores.exists() is False
    assert fs_plugin.translations.exists() is False


@pytest.mark.django
def test_plugin_instance_bad_args(fs_plugin):

    with pytest.raises(TypeError):
        fs_plugin.__class__()

    with pytest.raises(TypeError):
        fs_plugin.__class__("FOO")


@pytest.mark.django
def test_plugin_pull(fs_plugin):
    assert fs_plugin.is_cloned is False
    fs_plugin.pull()
    assert fs_plugin.is_cloned is True


@pytest.mark.django
def test_plugin_read_config(fs_plugin):
    config = fs_plugin.read_config()
    assert isinstance(config, ConfigParser)
    assert config.sections() == ['default', 'subdir1', 'subdir2', 'subdir3']


@pytest.mark.django
def test_plugin_find_translations(fs_plugin_pulled, expected_fs_stores):
    plugin = fs_plugin_pulled
    assert plugin.status().has_changed is False
    # test that Store objects have been created/updated


@pytest.mark.django
def test_plugin_push_translations(fs_plugin_pulled, expected_fs_stores):
    plugin = fs_plugin_pulled

    # add a Store object
    sibling = plugin.stores.get(
        pootle_path="/en/tutorial/subdir1/example1.po")
    Store.objects.create(
        parent=sibling.parent,
        translation_project=sibling.translation_project,
        name="example5.po")

    status = plugin.status()
    assert status.has_changed is True
    assert len(status["pootle_untracked"]) == 1

    plugin.add_translations()

    status = plugin.status()
    assert status.has_changed is True
    assert len(status["pootle_added"]) == 1

    plugin.push_translations()
    status = plugin.status()
    assert status.has_changed is False


@pytest.mark.django
def test_plugin_untracked_conflict_pootle_wins(fs_plugin_conflict_untracked):
    plugin = fs_plugin_conflict_untracked
    conflict = plugin.status()['conflict_untracked']
    assert conflict

    # add_translations wont add the conflicted file
    plugin.add_translations()
    _test_status(plugin, dict(conflict_untracked=conflict))

    # but add_translations with ``force`` will
    plugin.add_translations(force=True)
    _test_status(
        plugin,
        dict(
            pootle_added=[
                StoreFS.objects.get(
                    pootle_path=u'/en/tutorial/en.po',
                    path='/po/en.po')]))


@pytest.mark.django
def test_plugin_untracked_conflict_fs_wins(fs_plugin_conflict_untracked):
    plugin = fs_plugin_conflict_untracked
    conflict = plugin.status()['conflict_untracked']
    assert conflict

    # fetch_translations wont add the conflicted file
    plugin.fetch_translations()
    _test_status(plugin, dict(conflict_untracked=conflict))

    # but fetch_translations with ``force`` will
    plugin.fetch_translations(force=True)
    _test_status(
        plugin,
        dict(
            fs_added=[
                StoreFS.objects.get(
                    pootle_path=u'/en/tutorial/en.po',
                    path='/po/en.po')]))


@pytest.mark.django
def test_plugin_conflict_pootle_wins(fs_plugin_pulled, system):
    plugin = fs_plugin_pulled
    _edit_file(plugin, "gnu_style/po/en.po")
    _update_store(plugin)

    conflict = plugin.status()["conflict"]
    assert conflict

    # add_translations wont add the conflicted file
    plugin.add_translations()
    _test_status(plugin, dict(conflict=conflict))

    # but it will if we force
    plugin.add_translations(force=True)
    _test_status(
        plugin,
        dict(
            pootle_ahead=[
                StoreFS.objects.get(
                    pootle_path=u'/en/tutorial/en.po',
                    path='/gnu_style/po/en.po')]))


@pytest.mark.django
def test_plugin_conflict_fs_wins(fs_plugin_pulled, system):
    plugin = fs_plugin_pulled

    _edit_file(plugin, "gnu_style/po/en.po")
    _update_store(plugin)

    conflict = plugin.status()["conflict"]
    assert conflict

    # fetch_translations wont add the conflicted file
    plugin.fetch_translations()
    _test_status(plugin, dict(conflict=conflict))

    # but it will if we force
    plugin.fetch_translations(force=True)
    _test_status(
        plugin,
        dict(
            fs_ahead=[
                StoreFS.objects.get(
                    pootle_path=u'/en/tutorial/en.po',
                    path='/gnu_style/po/en.po')]))


########
# TODO:
@pytest.mark.django
def test_plugin_add_translations_path(fs_plugin_pulled):
    plugin = fs_plugin_pulled
    _setup_store(plugin, "subdir1/example5.po")
    plugin.add_translations(
        pootle_path="/en/tutorial/subdir1/*", fs_path="foo/nbar")


@pytest.mark.django
def test_plugin_push_translations_path(fs_plugin_pulled):
    plugin = fs_plugin_pulled
    _setup_store(plugin, "subdir1/example5.po")
    plugin.add_translations()
    plugin.push_translations(fs_path='/gnu_style/*')


@pytest.mark.django
def test_plugin_fetch_translations_path(fs_plugin_pulled):
    plugin = fs_plugin_pulled
    _edit_file(plugin, "gnu_style/po/en.po")
    plugin.fetch_translations(
        pootle_path="/en/tutorial/subdir1/*", fs_path="foo/nbar")


@pytest.mark.django
def test_plugin_pull_translations_path(fs_plugin_pulled):
    plugin = fs_plugin_pulled
    _edit_file(plugin, "gnu_style/po/en.po")
    plugin.fetch_translations(force=True)
    plugin.pull_translations(
        pootle_path="/en/tutorial/subdir1/*", fs_path="foo/nbar")
