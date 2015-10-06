from .finder import (
    BAD_FINDER_PATHS, ROOT_PATHS, FINDER_REGEXES, FILES, MATCHES)
from .plugin import PLUGIN_FETCH_PATHS, CONFLICT
from .status import PLUGIN_STATUS


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
