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

from ..fixtures.pootle_fs_fixtures import _fake_pull


@pytest.mark.django
def test_plugin_instance(example_plugin):
    assert example_plugin.project == example_plugin.fs.project
    assert example_plugin.local_fs_path.endswith(example_plugin.project.code)
    assert example_plugin.is_cloned is False
    assert example_plugin.stores.exists() is False
    assert example_plugin.translations.exists() is False


@pytest.mark.django
def test_plugin_instance_bad_args(example_plugin):

    with pytest.raises(TypeError):
        example_plugin.__class__()

    with pytest.raises(TypeError):
        example_plugin.__class__("FOO")


@pytest.mark.django
def test_plugin_pull(example_plugin):
    assert example_plugin.is_cloned is False
    _fake_pull(example_plugin.local_fs_path)
    assert example_plugin.is_cloned is True


@pytest.mark.django
def test_plugin_read_config(example_plugin):
    _fake_pull(example_plugin.local_fs_path)
    config = example_plugin.read_config()
    assert isinstance(config, ConfigParser)
    assert config.sections() == ['default', 'subdir1', 'subdir2', 'subdir3']


@pytest.mark.django
def test_plugin_find_translations(example_plugin, english,
                                  zulu, expected_fs_stores):
    _fake_pull(example_plugin.local_fs_path)
    assert (
        sorted(expected_fs_stores)
        == sorted(f for f in example_plugin.find_translations()))


@pytest.mark.django
def test_plugin_fetch_translations(example_plugin, english,
                                   zulu, expected_fs_stores):
    _fake_pull(example_plugin.local_fs_path)
    example_plugin.fetch_translations()
    from pootle_fs.models import StoreFS
    assert (
        sorted(expected_fs_stores)
        == sorted(StoreFS.objects.values_list("pootle_path", "path")))


@pytest.mark.django
def test_plugin_status(example_plugin, english, zulu, expected_fs_stores):
    status = example_plugin.status()
    from pootle_fs.plugin import ProjectFSStatus
    from pootle_fs.models import StoreFS
    status_types = [
        "pootle_ahead", "pootle_added",
        "fs_ahead", "fs_added", "conflict"]
    assert isinstance(status, ProjectFSStatus)
    assert str(status) == (
        "<ProjectFSStatus(Tutorial): Everything up-to-date>")
    assert status.has_changed is False
    for k in status_types:
        assert status[k] == set()
        assert k not in status

    _fake_pull(example_plugin.local_fs_path)
    example_plugin.fetch_translations()
    status = example_plugin.status()

    assert "fs_added" in status
    assert len(status["fs_added"]) == len(expected_fs_stores)
    assert isinstance([x for x in status['fs_added']][0], StoreFS)


@pytest.mark.django
def test_plugin_add_translations(example_plugin, english, zulu,
                                 expected_fs_stores):
    _fake_pull(example_plugin.local_fs_path)
    example_plugin.fetch_translations()
