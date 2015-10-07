from .fixtures.base import (
    root, projects, english, zulu, tutorial, english_tutorial, po_directory,
    english_tutorial_fs, en_tutorial_po, en_tutorial_fs_po, system,
    tutorial_fs, en_tutorial_po_fs_store, delete_pattern, fs_plugin)
(root, projects, english, zulu, tutorial, english_tutorial, po_directory,
 english_tutorial_fs, en_tutorial_po, en_tutorial_fs_po, system,
 tutorial_fs, en_tutorial_po_fs_store, delete_pattern, fs_plugin)
from .fixtures.finder import (
    BAD_FINDER_PATHS, ROOT_PATHS, FINDER_REGEXES, FILES, MATCHES,
    finder_files, fs_finder, finder_matches, finder_root_paths)
(finder_files, fs_finder, finder_matches, finder_root_paths)
from .fixtures.plugin import (
    PLUGIN_FETCH_PATHS, CONFLICT,
    expected_fs_stores, fs_fetch_paths, fs_plugin_conflicted_param,
    fs_plugin_fetched, fs_plugin_pulled)
(expected_fs_stores, fs_fetch_paths, fs_plugin_conflicted_param,
 fs_plugin_fetched, fs_plugin_pulled)
from .fixtures.status import PLUGIN_STATUS, fs_status
fs_status


PARAMETERS = (
    ("bad_finder_paths", BAD_FINDER_PATHS),
    ("root_paths", ROOT_PATHS),
    ("finder_regexes", FINDER_REGEXES),
    ("files", FILES),
    ("matches", MATCHES),
    ("plugin_fetch_paths", PLUGIN_FETCH_PATHS),
    ("plugin_status", PLUGIN_STATUS),
    ("conflict_outcomes", CONFLICT))


def pytest_generate_tests(metafunc):
    for name, params in PARAMETERS:
        if name in metafunc.fixturenames:
            metafunc.parametrize(name, params)
