#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest
from ConfigParser import ConfigParser

from pootle_fs_pytest.suite import (
    run_fetch_test, run_add_test, run_rm_test, run_merge_test)


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
def test_plugin_instance(fs_plugin):
    assert fs_plugin.project == fs_plugin.fs.project
    assert fs_plugin.local_fs_path.endswith(fs_plugin.project.code)
    assert fs_plugin.is_cloned is False
    assert fs_plugin.stores.exists() is False
    assert fs_plugin.translations.exists() is False


@pytest.mark.django
def test_plugin_read_config(fs_plugin):
    fs_plugin.pull()
    config = fs_plugin.read_config()
    assert isinstance(config, ConfigParser)
    assert config.sections() == ['default', 'subdir1', 'subdir2', 'subdir3']
    fs_plugin.fs.current_config.seek(0)
    current = fs_plugin.fs.current_config.read()
    fs_config = fs_plugin.read(fs_plugin.fs.pootle_config)
    assert current == fs_config


@pytest.mark.django
def test_plugin_pootle_attribution(fs_plugin_suite, member):
    plugin = fs_plugin_suite
    status = plugin.status()

    config = plugin.read_config()
    assert not config.has_option("default", "pootle_user")

    init_revs = {}
    for fs_status in status["fs_ahead"]:
        init_revs[fs_status.pootle_path] = (
            fs_status.store_fs.store.get_max_unit_revision())
    response = plugin.sync_translations()
    for action in response["pulled_to_pootle"]:
        changed_units = action.store.units.filter(
            revision__gt=init_revs[action.store.pootle_path])
        for unit in changed_units:
            if unit.target:
                assert unit.submitted_by.username == "system"
    config.set("default", "pootle_user", "member")
    config.write(
        open(
            os.path.join(plugin.fs.url, ".pootle.ini"), "w"))
    plugin.update_config()
    plugin.fetch_translations()
    status = plugin.status()
    updated_revs = {}
    for fs_status in status["fs_added"]:
        if fs_status.store_fs.store:
            updated_revs[fs_status.pootle_path] = (
                fs_status.store_fs.store.get_max_unit_revision())
        else:
            updated_revs[fs_status.pootle_path] = 0

    response = plugin.sync_translations()
    for action in response["pulled_to_pootle"]:
        changed_units = action.store.units.filter(
            revision__gt=updated_revs.get(action.store.pootle_path, 0))
        for unit in changed_units:
            if unit.target:
                assert unit.submitted_by.username == "member"


# Parametrized FETCH
@pytest.mark.django
def test_plugin_fetch(fs_plugin_suite, fetch_translations):
    run_fetch_test(fs_plugin_suite, **fetch_translations)


# Parametrized ADD
@pytest.mark.django
def test_plugin_add(fs_plugin_suite, add_translations):
    run_add_test(fs_plugin_suite, **add_translations)


# Parametrized RM
@pytest.mark.django
def test_plugin_rm(fs_plugin_suite, rm_translations):
    run_rm_test(fs_plugin_suite, **rm_translations)


# Parametrized MERGE
@pytest.mark.django
def test_plugin_merge_fs(fs_plugin_suite, merge_translations):
    run_merge_test(fs_plugin_suite, **merge_translations)


# Parametrized MERGE
@pytest.mark.django
def test_plugin_merge_pootle(fs_plugin_suite, merge_translations):
    run_merge_test(
        fs_plugin_suite,
        pootle_wins=True,
        **merge_translations)
