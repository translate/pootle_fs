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

from pootle_store.models import Store


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
    example_plugin.pull()
    assert example_plugin.is_cloned is True


@pytest.mark.django
def test_plugin_read_config(example_plugin):
    config = example_plugin.read_config()
    assert isinstance(config, ConfigParser)
    assert config.sections() == ['default', 'subdir1', 'subdir2', 'subdir3']


@pytest.mark.django
def test_plugin_find_translations(example_plugin, english,
                                  zulu, expected_fs_stores):
    assert (
        sorted(expected_fs_stores)
        == sorted(f for f in example_plugin.find_translations()))


@pytest.mark.django
def test_plugin_fetch_translations(example_plugin, english,
                                   zulu, expected_fs_stores):
    example_plugin.fetch_translations()
    from pootle_fs.models import StoreFS
    assert (
        sorted(expected_fs_stores)
        == sorted(StoreFS.objects.values_list("pootle_path", "path")))


@pytest.mark.django
def test_plugin_status(example_plugin, english, zulu, expected_fs_stores):
    from pootle_fs.plugin import ProjectFSStatus
    from pootle_fs.models import StoreFS

    assert example_plugin.is_cloned is False
    status = example_plugin.status()

    # calling status will call pull
    assert example_plugin.is_cloned is True

    status_types = [
        "pootle_ahead", "pootle_added",
        "fs_ahead", "fs_added", "conflict"]
    assert isinstance(status, ProjectFSStatus)
    assert str(status) == (
        "<ProjectFSStatus(Tutorial): fs_new: 18>")
    assert status.has_changed is True
    for k in status_types:
        if k == "fs_new":
            continue
        assert status[k] == set()
        assert k not in status
    assert sorted(status['fs_new']) == sorted(expected_fs_stores)

    # when we fetch the translations their status is set to fs_added
    example_plugin.fetch_translations()
    status = example_plugin.status()
    assert "fs_added" in status
    assert len(status["fs_added"]) == len(expected_fs_stores)
    assert all([isinstance(x, StoreFS) for x in status['fs_added']])

    # pulling the translations makes us up-to-date
    example_plugin.pull_translations()
    status = example_plugin.status()
    assert status.has_changed is False


@pytest.mark.django
def test_plugin_status_add_fs_not_matching(example_plugin, english,
                                           zulu, expected_fs_stores):
    example_plugin.fetch_translations()
    example_plugin.pull_translations()
    status = example_plugin.status()
    assert status.has_changed is False

    # add another file - not matched in config
    with open(os.path.join(example_plugin.local_fs_path, "foo.po"), "w") as f:
        f.write(" ")

    example_plugin.fetch_translations()
    status = example_plugin.status()
    assert status.has_changed is False


@pytest.mark.django
def test_plugin_status_add_fs(example_plugin, english,
                              zulu, expected_fs_stores):
    example_plugin.fetch_translations()
    example_plugin.pull_translations()
    status = example_plugin.status()
    assert status.has_changed is False

    # add another file - matched in config
    new_file = "gnu_style_named_files/po/example5-en.po"
    with open(os.path.join(example_plugin.local_fs_path, new_file), "w") as f:
        f.write(" ")

    example_plugin.fetch_translations()
    status = example_plugin.status()
    assert status.has_changed is True
    assert len(status["fs_added"]) == 1


@pytest.mark.django
def test_plugin_add_translations(example_plugin, english, zulu,
                                 expected_fs_stores):
    example_plugin.fetch_translations()


@pytest.mark.django
def test_plugin_pull_translations(example_plugin, english, zulu,
                                  expected_fs_stores):
    example_plugin.fetch_translations()
    example_plugin.pull_translations()
    assert example_plugin.status().has_changed is False

    # test that Store objects have been created/updated


@pytest.mark.django
def test_plugin_push_translations(example_plugin, english, zulu,
                                  expected_fs_stores):
    example_plugin.fetch_translations()
    example_plugin.pull_translations()
    assert example_plugin.status().has_changed is False

    # add a Store object
    sibling = example_plugin.stores.get(
        pootle_path="/en/tutorial/subdir1/example1")
    Store.objects.create(
        parent=sibling.parent,
        translation_project=sibling.translation_project,
        name="example5.po")

    status = example_plugin.status()
    assert status.has_changed is True
    assert len(status["pootle_new"]) == 1

    example_plugin.add_translations()

    status = example_plugin.status()
    assert status.has_changed is True
    assert len(status["pootle_added"]) == 1

    example_plugin.push_translations()
    status = example_plugin.status()
    assert status.has_changed is False
