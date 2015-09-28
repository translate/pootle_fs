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
import shutil


def _fake_pull(dir_path, project_fs, src="../../data/fs/example_fs"):
    shutil.copytree(
        os.path.abspath(
            os.path.join(
                __file__,
                src)),
        os.path.join(dir_path, project_fs.project.code))


@pytest.mark.django
def test_plugin_instance(tutorial_fs, example_plugin, tmpdir, settings):
    dir_path = str(tmpdir.dirpath())
    settings.POOTLE_FS_PATH = dir_path
    plugin = example_plugin(tutorial_fs)

    assert plugin.project == tutorial_fs.project
    assert plugin.fs == tutorial_fs
    assert plugin.local_fs_path == os.path.join(
        dir_path, tutorial_fs.project.code)
    assert plugin.is_cloned is False
    assert plugin.stores.exists() is False
    assert plugin.translations.exists() is False
    assert plugin.name == example_plugin.name


@pytest.mark.django
def test_plugin_instance_bad_args(example_plugin):

    with pytest.raises(TypeError):
        example_plugin()

    with pytest.raises(TypeError):
        example_plugin("FOO")


@pytest.mark.django
def test_plugin_pull(tutorial_fs, example_plugin, tmpdir, settings):
    dir_path = str(tmpdir.dirpath())
    settings.POOTLE_FS_PATH = dir_path
    plugin = example_plugin(tutorial_fs)
    _fake_pull(dir_path, tutorial_fs)
    assert plugin.is_cloned is True
