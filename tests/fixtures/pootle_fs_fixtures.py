#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import datetime
from md5 import md5
import os
import pytest
import shutil


EXAMPLE_FS = os.path.join(__file__, "../../data/fs/example_fs")
STATUS_TYPES = [
    "pootle_ahead", "pootle_added", "pootle_untracked", "pootle_removed",
    "fs_ahead", "fs_added", "fs_untracked", "fs_removed",
    "conflict", "conflict_untracked"]


def _test_status(plugin, expected):
    status = plugin.status()
    assert status.has_changed is (expected and True or False)
    for k in STATUS_TYPES:
        if k in expected:
            assert status[k] == expected[k]
            assert k in status
        else:
            assert status[k] == []
            assert k not in status


def _edit_file(plugin, filepath):
    po_file = (os.path.join(plugin.local_fs_path, filepath))
    with open(po_file, "w") as f:
        f.write(str(datetime.now()))


def _remove_file(plugin, path):
    # remove the file from FS
    os.unlink(os.path.join(plugin.local_fs_path, path))


def _update_store(plugin):
    from pootle_store.models import Unit
    # Update the store revision
    store = plugin.stores.first()
    Unit.objects.create(
        unitid="Foo", store=store, index=0, revision=1)


def _remove_store(plugin):
    # Remove the store
    plugin.stores[0].delete()


def _clear_plugins():
    from pootle_fs import plugins
    plugins.__plugins__ = {}


def _register_plugin(name="example", plugin=None, clear=True, src=EXAMPLE_FS):
    if clear:
        _clear_plugins()

    from pootle_fs import Plugin, plugins, FSFile

    class ExampleFSFile(FSFile):

        @property
        def latest_hash(self):
            if self.exists:
                return md5(str(os.stat(self.file_path).st_mtime)).hexdigest()

    class ExamplePlugin(Plugin):

        file_class = ExampleFSFile
        _pulled = False

        def pull(self):
            dir_path = self.local_fs_path
            if not self._pulled:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                shutil.copytree(
                    os.path.abspath(
                        os.path.join(
                            __file__,
                            src)),
                    os.path.abspath(dir_path))
            self._pulled = True

    ExamplePlugin.name = name
    plugins.register(plugin or ExamplePlugin)
    return ExamplePlugin


def _fake_pull(dir_path, src=EXAMPLE_FS):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    shutil.copytree(
        os.path.abspath(
            os.path.join(
                __file__,
                src)),
        os.path.abspath(dir_path))


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
def tmp_pootle_fs(tmpdir):
    dir_path = os.path.join(str(tmpdir.dirpath()), "example_fs")
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    _fake_pull(dir_path)
    return tmpdir


@pytest.fixture
def expected_fs_stores():
    return [
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


po_config = """
[default]
translation_path = po/<lang>.po
"""


def _setup_dir(dir_path, makepo=True):
    src = os.path.join(dir_path, "src")
    if os.path.exists(src):
        shutil.rmtree(src)
    po_path = os.path.join(src, "po")
    os.makedirs(po_path)
    if makepo:
        with open(os.path.join(po_path, "en.po"), "w") as f:
            f.write(" ")
    with open(os.path.join(src, ".pootle.ini"), "w") as f:
        f.write(po_config)
    return src


def _setup_store(tutorial_fs, path="en.po"):
    from pootle_store.models import Store
    tp = tutorial_fs.project.translationproject_set.get(
        language__code="en")
    parts = path.strip("/").split("/")
    directory = tp.directory
    for part in parts[:-1]:
        directory = directory.child_dirs.get(name=part)
    store = Store.objects.create(
        translation_project=tp, parent=directory, name=parts[-1])
    return store


def _clear_fs(dir_path, tutorial_fs):
    tutorial_path = os.path.join(dir_path, tutorial_fs.project.code)
    if os.path.exists(tutorial_path):
        shutil.rmtree(tutorial_path)


@pytest.fixture
def fs_plugin_conflict_untracked(tutorial_fs, tmpdir, settings):
    dir_path = str(tmpdir.dirpath())
    _clear_fs(dir_path, tutorial_fs)
    _setup_store(tutorial_fs)
    plugin = _register_plugin(src=_setup_dir(dir_path))
    settings.POOTLE_FS_PATH = dir_path
    return plugin(tutorial_fs)


@pytest.fixture
def fs_plugin_fs_untracked(tutorial_fs, tmpdir, settings):
    dir_path = str(tmpdir.dirpath())
    _clear_fs(dir_path, tutorial_fs)
    plugin = _register_plugin(src=_setup_dir(dir_path))
    settings.POOTLE_FS_PATH = dir_path
    return plugin(tutorial_fs)


@pytest.fixture
def fs_plugin_pootle_untracked(tutorial_fs, tmpdir, settings):
    dir_path = str(tmpdir.dirpath())
    _clear_fs(dir_path, tutorial_fs)
    _setup_store(tutorial_fs)
    plugin = _register_plugin(src=_setup_dir(dir_path, makepo=False))
    settings.POOTLE_FS_PATH = dir_path
    return plugin(tutorial_fs)


@pytest.fixture
def fs_plugin_fetched(fs_plugin, english, zulu):
    fs_plugin.fetch_translations()
    return fs_plugin


@pytest.fixture
def fs_plugin_pulled(fs_plugin_fetched):
    fs_plugin_fetched.pull_translations()
    return fs_plugin_fetched
