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
