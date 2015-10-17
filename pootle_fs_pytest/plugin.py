from .fixtures.base import (
    root, projects, english, zulu, tutorial, english_tutorial, po_directory,
    english_tutorial_fs, en_tutorial_po, en_tutorial_fs_po, system, member,
    tutorial_fs, en_tutorial_po_fs_store, delete_pattern)
(root, projects, english, zulu, tutorial, english_tutorial, po_directory,
 english_tutorial_fs, en_tutorial_po, en_tutorial_fs_po, system, member,
 tutorial_fs, en_tutorial_po_fs_store, delete_pattern)

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
