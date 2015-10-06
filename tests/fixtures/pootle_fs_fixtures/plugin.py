#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict
import os
import shutil

import pytest

from .utils import (
    _clear_fs, _edit_file, _register_plugin, _setup_dir, _setup_store,
    _update_store)

STATUS_TYPES = [
    "pootle_ahead", "pootle_added", "pootle_untracked", "pootle_removed",
    "fs_ahead", "fs_added", "fs_untracked", "fs_removed",
    "conflict", "conflict_untracked"]

EXPECTED_FS_STORES = [
    (u'/en/tutorial/en.po',
     '/gnu_style/po/en.po'),
    (u'/en/tutorial/subdir1/example1.po',
     '/gnu_style_named_folders/po-example1/en.po'),
    (u'/en/tutorial/subdir1/example2.po',
     '/gnu_style_named_folders/po-example2/en.po'),
    (u'/en/tutorial/subdir2/example1.po',
     '/gnu_style_named_files/po/example1-en.po'),
    (u'/en/tutorial/subdir2/example2.po',
     '/gnu_style_named_files/po/example2-en.po'),
    (u'/en/tutorial/subdir3/example1.po',
     '/non_gnu_style/locales/en/example1.po'),
    (u'/en/tutorial/subdir3/example2.po',
     '/non_gnu_style/locales/en/example2.po'),
    (u'/en/tutorial/subdir3/subsubdir/example3.po',
     '/non_gnu_style/locales/en/subsubdir/example3.po'),
    (u'/en/tutorial/subdir3/subsubdir/example4.po',
     '/non_gnu_style/locales/en/subsubdir/example4.po'),
    (u'/zu/tutorial/zu.po',
     '/gnu_style/po/zu.po'),
    (u'/zu/tutorial/subdir1/example1.po',
     '/gnu_style_named_folders/po-example1/zu.po'),
    (u'/zu/tutorial/subdir1/example2.po',
     '/gnu_style_named_folders/po-example2/zu.po'),
    (u'/zu/tutorial/subdir2/example1.po',
     '/gnu_style_named_files/po/example1-zu.po'),
    (u'/zu/tutorial/subdir2/example2.po',
     '/gnu_style_named_files/po/example2-zu.po'),
    (u'/zu/tutorial/subdir3/example1.po',
     '/non_gnu_style/locales/zu/example1.po'),
    (u'/zu/tutorial/subdir3/example2.po',
     '/non_gnu_style/locales/zu/example2.po'),
    (u'/zu/tutorial/subdir3/subsubdir/example3.po',
     '/non_gnu_style/locales/zu/subsubdir/example3.po'),
    (u'/zu/tutorial/subdir3/subsubdir/example4.po',
     '/non_gnu_style/locales/zu/subsubdir/example4.po')]

CONFLICT = OrderedDict()
CONFLICT['conflict_add'] = (
    lambda plugin: plugin.add_translations(), None)
CONFLICT['conflict_add_force'] = (
    lambda plugin: plugin.add_translations(force=True),
    dict(pootle_ahead=[(u'/en/tutorial/en.po', '/gnu_style/po/en.po')]))
CONFLICT['conflict_fetch'] = (
    lambda plugin: plugin.fetch_translations(), None)
CONFLICT['conflict_fetch_force'] = (
    lambda plugin: plugin.fetch_translations(force=True),
    dict(fs_ahead=[(u'/en/tutorial/en.po', '/gnu_style/po/en.po')]))
CONFLICT['conflict_untracked_add'] = (
    lambda plugin: plugin.add_translations(), None)
CONFLICT['conflict_untracked_add_force'] = (
    lambda plugin: plugin.add_translations(force=True),
    dict(pootle_added=[(u'/en/tutorial/en.po', '/po/en.po')]))
CONFLICT['conflict_untracked_fetch'] = (
    lambda plugin: plugin.fetch_translations(), None)
CONFLICT['conflict_untracked_fetch_force'] = (
    lambda plugin: plugin.fetch_translations(force=True),
    dict(fs_added=[(u'/en/tutorial/en.po', '/po/en.po')]))

PLUGIN_FETCH_PATHS = OrderedDict()
PLUGIN_FETCH_PATHS["fetch_pootle_path_bad_short"] = (
    dict(pootle_path="/en/tutorial"),
    dict(fs_untracked=1))
PLUGIN_FETCH_PATHS["fetch_pootle_path_bad_no_slash"] = (
    dict(pootle_path="en/tutorial/*"),
    dict(fs_untracked=1))
PLUGIN_FETCH_PATHS["fetch_pootle_path_good"] = (
    dict(pootle_path="/en/tutorial/*"),
    dict(fs_added=1))


@pytest.fixture
def expected_fs_stores():
    return EXPECTED_FS_STORES


@pytest.fixture
def fs_fetch_paths(fs_plugin_pulled, plugin_fetch_paths, system):
    _edit_file(fs_plugin_pulled, "non_gnu_style/locales/en/foo/bar/baz.po")
    return [fs_plugin_pulled] + list(PLUGIN_FETCH_PATHS[plugin_fetch_paths])


@pytest.fixture
def fs_plugin(tutorial_fs, tmpdir, settings):
    plugin = _register_plugin()
    dir_path = str(tmpdir.dirpath())
    settings.POOTLE_FS_PATH = dir_path
    tutorial_path = os.path.join(dir_path, tutorial_fs.project.code)
    if os.path.exists(tutorial_path):
        shutil.rmtree(tutorial_path)
    return plugin(tutorial_fs)


@pytest.fixture
def fs_plugin_conflicted_param(conflict_outcomes, tutorial_fs,
                               tmpdir, settings, system):
    dir_path = str(tmpdir.dirpath())
    settings.POOTLE_FS_PATH = dir_path
    _clear_fs(dir_path, tutorial_fs)
    if conflict_outcomes.startswith("conflict_untracked"):
        plugin = _register_plugin(src=_setup_dir(dir_path))
    else:
        plugin = _register_plugin()

    plugin = plugin(tutorial_fs)
    if conflict_outcomes.startswith("conflict_untracked"):
        _setup_store(tutorial_fs)
    else:
        plugin.fetch_translations()
        plugin.pull_translations()
        _edit_file(plugin, "gnu_style/po/en.po")
        _update_store(plugin)

    return ([conflict_outcomes, plugin]
            + list(CONFLICT[conflict_outcomes]))


@pytest.fixture
def fs_plugin_fetched(fs_plugin, english, zulu):
    fs_plugin.fetch_translations()
    return fs_plugin


@pytest.fixture
def fs_plugin_pulled(fs_plugin_fetched):
    fs_plugin_fetched.pull_translations()
    return fs_plugin_fetched
