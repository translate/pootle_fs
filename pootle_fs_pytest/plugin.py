# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from .fixtures.base import (
    root, projects, english, zulu, spanish, tutorial, english_tutorial,
    po_directory, english_tutorial_fs, en_tutorial_po, en_tutorial_fs_po,
    system, member, tutorial_fs, en_tutorial_po_fs_store, delete_pattern,
    other_project)
(root, projects, english, spanish, zulu, tutorial, english_tutorial,
 po_directory, english_tutorial_fs, en_tutorial_po, en_tutorial_fs_po, system,
 member, tutorial_fs, en_tutorial_po_fs_store, delete_pattern, other_project)

from .fixtures.finder import (
    BAD_FINDER_PATHS, ROOT_PATHS, FINDER_REGEXES, FILES, MATCHES,
    finder_files, fs_finder, finder_matches, finder_root_paths)
(finder_files, fs_finder, finder_matches, finder_root_paths)

from .fixtures.plugin import (
    ADD, FETCH, RM, MERGE,
    fs_plugin, fs_plugin_base, fs_plugin_suite, fs_plugin_synced,
    add_translations, fetch_translations, rm_translations, merge_translations)
(fs_plugin, fs_plugin_base, fs_plugin_suite, fs_plugin_synced,
 fetch_translations, add_translations, rm_translations,
 merge_translations)

from .fixtures.status import PLUGIN_STATUS, fs_status
fs_status


PARAMETERS = (
    ("bad_finder_paths", BAD_FINDER_PATHS),
    ("root_paths", ROOT_PATHS),
    ("finder_regexes", FINDER_REGEXES),
    ("files", FILES),
    ("matches", MATCHES),
    ("add", ADD),
    ("rm", RM),
    ("merge", MERGE),
    ("fetch", FETCH),
    ("plugin_status", PLUGIN_STATUS))


def pytest_generate_tests(metafunc):
    for name, params in PARAMETERS:
        if name in metafunc.fixturenames:
            metafunc.parametrize(name, params)
