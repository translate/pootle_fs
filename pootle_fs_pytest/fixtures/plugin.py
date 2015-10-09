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

from pootle_fs_pytest.utils import (
    create_test_suite, create_plugin, _register_plugin)


_plugin_fetch_base = {
    'conflict': 1,
    'conflict_untracked': 1,
    'fs_ahead': 1,
    'fs_removed': 1,
    'fs_untracked': 2,
    'pootle_ahead': 1,
    'pootle_removed': 1,
    'pootle_untracked': 1}

FETCH_PATHS = [
    ("all", None, None),
    ("pp_short", "/en/tutorial", None),
    ("pp_no_slash", "en/tutorial/*", None),
    ("pp_all", "/*", None),
    ("pp_langs", "/[ez][nu]/tutorial/*", None),
    ("pp_pofile", "/en/tutorial/subdir1/example10.po", None),
    ("pp_podir", "/en/tutorial/*example10*", None),
    ("pp_conflict", "/zu/tutorial/subdir3/subsubdir/example4.po", None),
    ("pp_conflict_untracked", "/subdir3/subsubdir/example5.po", None),
    ("fs_short", None, "/gnu_style_named_folders"),
    ("fs_no_slash", None, "en/tutorial/*"),
    ("fs_all", None, "/*"),
    ("fs_gnu", None, "/*gnu*/*"),
    ("fs_en", None, "/gnu_style/*en*"),
    ("fs_en.po", None, "/gnu_style/po/en.po")]


def _generate_fetch_fixtures():
    fetch = OrderedDict()
    for test, pootle_path, fs_path in FETCH_PATHS:
        fetch[test] = {
            "pootle_path": pootle_path,
            "fs_path": fs_path}
    return fetch


def _generate_add_fixtures():
    add = OrderedDict()
    for test, pootle_path, fs_path in FETCH_PATHS:
        add[test] = {
            "pootle_path": pootle_path,
            "fs_path": fs_path}
    return add


def _generate_pull_fixtures():
    pull = OrderedDict()
    for test, pootle_path, fs_path in FETCH_PATHS:
        pull[test] = {
            "pootle_path": pootle_path,
            "fs_path": fs_path}
    return pull


def _generate_push_fixtures():
    push = OrderedDict()
    for test, pootle_path, fs_path in FETCH_PATHS:
        push[test] = {
            "pootle_path": pootle_path,
            "fs_path": fs_path}
    return push

FETCH = _generate_fetch_fixtures()
ADD = _generate_add_fixtures()
PULL = _generate_pull_fixtures()
PUSH = _generate_push_fixtures()


@pytest.fixture
def fs_plugin_suite(fs_plugin):
    return create_test_suite(fs_plugin)


@pytest.fixture
def fetch_translations(fetch):
    return FETCH[fetch]


@pytest.fixture
def add_translations(add):
    return ADD[add]


@pytest.fixture
def pull_translations(pull):
    return PULL[pull]


@pytest.fixture
def push_translations(push):
    return PUSH[push]


@pytest.fixture
def fs_plugin(fs_plugin_base):
    tutorial, src_path, repo_path, dir_path = fs_plugin_base
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    os.makedirs(repo_path)
    for f in os.listdir(src_path):
        src = os.path.join(src_path, f)
        target = os.path.join(repo_path, f)
        if os.path.isdir(src):
            shutil.copytree(src, target)
        else:
            shutil.copyfile(src, target)
    _register_plugin("example")
    plugin = create_plugin("example", fs_plugin_base)
    return plugin


@pytest.fixture
def fs_plugin_base(tutorial, tmpdir, settings, system, english, zulu):
    import pootle_fs_pytest
    dir_path = str(tmpdir.dirpath())
    repo_path = os.path.join(dir_path, "__src__")
    src_path = os.path.abspath(
        os.path.join(
            os.path.dirname(pootle_fs_pytest.__file__),
            "data/fs/example_fs"))
    settings.POOTLE_FS_PATH = dir_path
    tutorial_path = os.path.join(dir_path, tutorial.code)
    if os.path.exists(tutorial_path):
        shutil.rmtree(tutorial_path)
    return tutorial, src_path, repo_path, dir_path


@pytest.fixture
def fs_plugin_pulled(fs_plugin):
    fs_plugin.fetch_translations()
    fs_plugin.pull_translations()
    return fs_plugin
