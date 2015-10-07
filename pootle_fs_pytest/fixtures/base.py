import os
import shutil
import tempfile

import pytest

from ..utils import (
    _require_language, _require_project, _require_tp, _require_store,
    _require_user, _register_plugin)


@pytest.fixture
def root(transactional_db):
    """Require the root directory."""
    from pootle_app.models import Directory
    root, created = Directory.objects.get_or_create(name='')
    return root


@pytest.fixture
def projects(root):
    """Require the projects directory."""
    from pootle_app.models import Directory
    projects, created = Directory.objects.get_or_create(name='projects',
                                                        parent=root)
    return projects


@pytest.fixture
def english(root):
    """Require the English language."""
    return _require_language('en', 'English')


@pytest.fixture
def zulu(root):
    """Require the English language."""
    return _require_language('zu', 'Zulu')


@pytest.fixture
def tutorial(projects, english):
    """Require `tutorial` test project."""
    return _require_project('tutorial', 'Tutorial', english)


@pytest.fixture
def english_tutorial(english, tutorial):
    """Require English Tutorial."""
    return _require_tp(english, tutorial)


@pytest.fixture(scope='session')
def po_directory(request):
    """Sets up a tmp directory with test PO files."""
    from django.conf import settings
    from pootle_store.models import fs

    test_base_dir = tempfile.mkdtemp()

    projects = [dirname for dirname
                in os.listdir(settings.POOTLE_TRANSLATION_DIRECTORY)
                if dirname != '.tmp']

    for project in projects:
        src_dir = os.path.join(settings.POOTLE_TRANSLATION_DIRECTORY, project)

        # Copy files over the temporal dir
        shutil.copytree(src_dir, os.path.join(test_base_dir, project))

    # Adjust locations
    settings.POOTLE_TRANSLATION_DIRECTORY = test_base_dir
    fs.location = test_base_dir

    def _cleanup():
        shutil.rmtree(test_base_dir)
    request.addfinalizer(_cleanup)

    return test_base_dir


@pytest.fixture
def english_tutorial_fs(english, tutorial):
    """Require English Tutorial."""
    _register_plugin()
    from pootle_fs.models import ProjectFS
    ProjectFS.objects.create(
        project=tutorial, fs_type="example")
    return _require_tp(english, tutorial)


@pytest.fixture
def en_tutorial_po(settings, english_tutorial, system):
    """Require the /en/tutorial/tutorial.po store."""
    return _require_store(english_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY, 'tutorial.po')


@pytest.fixture
def en_tutorial_fs_po(settings, english_tutorial_fs, system):
    """Require the /en/tutorial/tutorial.po store."""
    return _require_store(english_tutorial_fs,
                          settings.POOTLE_TRANSLATION_DIRECTORY, 'tutorial.po')


@pytest.fixture
def system(db):
    """Require the system user."""
    return _require_user('system', 'system user')


@pytest.fixture
def tutorial_fs(tutorial):
    from pootle_fs.models import ProjectFS
    return ProjectFS.objects.create(
        project=tutorial,
        fs_type="example",
        url=_register_plugin().src)


@pytest.fixture
def en_tutorial_po_fs_store(en_tutorial_fs_po):
    """Require the /en/tutorial/tutorial.po store."""
    from pootle_fs.models import StoreFS
    return StoreFS.objects.create(
        store=en_tutorial_fs_po,
        path="/some/fs/path")


@pytest.fixture(scope='session', autouse=True)
def delete_pattern():
    """Adds the no-op `delete_pattern()` method to `LocMemCache`."""
    from django.core.cache.backends.locmem import LocMemCache
    LocMemCache.delete_pattern = lambda x, y: 0


@pytest.fixture
def fs_plugin(tutorial_fs, tmpdir, settings, system, english, zulu):
    plugin = _register_plugin()
    dir_path = str(tmpdir.dirpath())
    settings.POOTLE_FS_PATH = dir_path
    tutorial_path = os.path.join(dir_path, tutorial_fs.project.code)
    if os.path.exists(tutorial_path):
        shutil.rmtree(tutorial_path)
    return plugin(tutorial_fs)
