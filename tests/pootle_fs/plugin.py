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

from pootle_fs.language import LanguageMapper


TEST_LANG_MAPPING = """
   en_FOO en
   es_FOO es
   zu_FOO zu
"""

TEST_LANG_MAPPING_BAD = """
   en_FOO en
   es_FOO es
   zu_FOO zu XXX
"""


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


@pytest.mark.django
def test_plugin_language_mapper(fs_plugin_suite, english):
    plugin = fs_plugin_suite
    config = plugin.read_config()
    assert not config.has_option("default", "lang_mapping")
    assert isinstance(plugin.lang_mapper, LanguageMapper)
    assert plugin.lang_mapper.lang_mappings == {}
    assert plugin.lang_mapper["en_FOO"] is None
    assert plugin.lang_mapper.get_pootle_code("en") == "en"
    assert plugin.lang_mapper.get_pootle_code("en_FOO") == "en_FOO"
    assert plugin.lang_mapper.get_fs_code("en") == "en"

    config.set("default", "lang_mapping", TEST_LANG_MAPPING)
    config.write(
        open(
            os.path.join(plugin.fs.url, ".pootle.ini"), "w"))
    plugin.update_config()
    assert config.has_option("default", "lang_mapping")
    assert plugin.lang_mapper.lang_mappings == {
        x.strip().split(" ")[0]: x.strip().split(" ")[1]
        for x in TEST_LANG_MAPPING.split("\n")
        if x.strip()}

    assert "en_FOO" in plugin.lang_mapper
    assert plugin.lang_mapper["en_FOO"] == english


@pytest.mark.django
def test_plugin_language_mapper_bad(fs_plugin_suite, zulu):
    plugin = fs_plugin_suite
    config = plugin.read_config()
    config.set("default", "lang_mapping", TEST_LANG_MAPPING_BAD)
    config.write(
        open(
            os.path.join(plugin.fs.url, ".pootle.ini"), "w"))
    plugin.update_config()
    # bad configuration lines are ignored
    assert plugin.lang_mapper.lang_mappings == {
        x.strip().split(" ")[0]: x.strip().split(" ")[1]
        for x in TEST_LANG_MAPPING.split("\n")
        if x.strip()
        and not x.strip().startswith("zu")}
    assert "zu_FOO" not in plugin.lang_mapper
    assert plugin.lang_mapper["zu_FOO"] is None
    assert plugin.lang_mapper["zu"] == zulu


# Parametrized ADD
@pytest.mark.django_db(transaction=True)
def test_plugin_add(fs_plugin_suite, add_translations):
    print "Running add test"
    run_add_test(fs_plugin_suite, **add_translations)


# Parametrized FETCH
@pytest.mark.django_db(transaction=True)
def test_plugin_fetch(fs_plugin_suite, fetch_translations):
    print "Running fetch test"
    run_fetch_test(fs_plugin_suite, **fetch_translations)


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
