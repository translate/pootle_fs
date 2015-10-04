#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict
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

BAD_FINDER_PATHS = [
    "lang/foo.po",
    "<lang>/<foo>.po",
    "../<lang>/foo.po",
    "<lang>/../foo.po",
    "<lang>/..",
    "foo/@<lang>/bar.po"]

ROOT_PATHS = OrderedDict()
ROOT_PATHS["<lang>.po"] = ""
ROOT_PATHS["foo/<lang>.po"] = "foo"
ROOT_PATHS["foo/bar/baz-<filename>-<lang>.po"] = "foo/bar"

MATCHES = OrderedDict()
MATCHES["po/<lang>.po"] = (
    ["en.po",  "foo/bar/en.po"],
    [("po/en.po", dict(lang="en"))])
MATCHES["po-<filename>/<lang>.po"] = (
    ["en.po",  "po/en.po"],
    [("po-foo/en.po", dict(lang="en", filename="foo"))])
MATCHES["po/<filename>-<lang>.po"] = (
    ["en.po",  "po/en.po"],
    [("po/foo-en.po", dict(lang="en", filename="foo"))])
MATCHES["<lang>/<directory_path>/<filename>.po"] = (
    ["foo.po"],
    [("en/foo.po",
      dict(lang="en", directory_path="", filename="foo")),
     ("en/bar/baz/foo.po",
      dict(lang="en", directory_path="bar/baz", filename="foo"))])
MATCHES["<directory_path>/<lang>/<filename>.po"] = (
    ["foo.po"],
    [("en/foo.po",
      dict(lang="en", directory_path="", filename="foo")),
     ("bar/baz/en/foo.po",
      dict(lang="en", directory_path="bar/baz", filename="foo"))])

FINDER_REGEXES = [
    "<lang>.po",
    "<lang>/<filename>.po",
    "<directory_path>/<lang>.po",
    "<lang><directory_path>/<filename>.po"]

FILES = OrderedDict()
FILES["gnu_style/po/<lang>.po"] = (
    ("gnu_style/po/zu.po",
     dict(lang="zu",
          directory_path="")),
    ("gnu_style/po/en.po",
     dict(lang="en",
          directory_path="")))
FILES["gnu_style_named_files/po/<filename>-<lang>.po"] = (
    ("gnu_style_named_files/po/example1-en.po",
     dict(lang="en",
          filename="example1.po",
          directory_path="")),
    ("gnu_style_named_files/po/example1-zu.po",
     dict(lang="zu",
          filename="example1.po",
          directory_path="")),
    ("gnu_style_named_files/po/example2-en.po",
     dict(lang="en",
          filename="example2.po",
          directory_path="")),
    ("gnu_style_named_files/po/example2-zu.po",
     dict(lang="zu",
          filename="example2.po",
          directory_path="")))
FILES["gnu_style_named_folders/po-<filename>/<lang>.po"] = (
    ("gnu_style_named_folders/po-example1/en.po",
     dict(lang="en",
          filename="example1.po",
          directory_path="")),
    ("gnu_style_named_folders/po-example1/zu.po",
     dict(lang="zu",
          filename="example1.po",
          directory_path="")),
    ("gnu_style_named_folders/po-example2/en.po",
     dict(lang="en",
          filename="example2.po",
          directory_path="")),
    ("gnu_style_named_folders/po-example2/zu.po",
     dict(lang="zu",
          filename="example2.po",
          directory_path="")))
FILES["non_gnu_style/locales/<lang>/<directory_path>/<filename>.po"] = (
    ("non_gnu_style/locales/en/example1.po",
     dict(lang="en",
          filename="example1.po",
          directory_path="")),
    ("non_gnu_style/locales/zu/example1.po",
     dict(lang="zu",
          filename="example1.po",
          directory_path="")),
    ("non_gnu_style/locales/en/example2.po",
     dict(lang="en",
          filename="example2.po",
          directory_path="")),
    ("non_gnu_style/locales/zu/example2.po",
     dict(lang="zu",
          filename="example2.po",
          directory_path="")),
    ("non_gnu_style/locales/en/subsubdir/example3.po",
     dict(lang="en",
          filename="example3.po",
          directory_path="subsubdir")),
    ("non_gnu_style/locales/zu/subsubdir/example3.po",
     dict(lang="zu",
          filename="example3.po",
          directory_path="subsubdir")),
    ("non_gnu_style/locales/en/subsubdir/example4.po",
     dict(lang="en",
          filename="example4.po",
          directory_path="subsubdir")),
    ("non_gnu_style/locales/zu/subsubdir/example4.po",
     dict(lang="zu",
          filename="example4.po",
          directory_path="subsubdir")))


def _create_conflict(plugin):
    _setup_store(
        plugin,
        path="subdir3/subsubdir/example5.po")
    _edit_file(
        plugin,
        "non_gnu_style/locales/en/subsubdir/example5.po")


PLUGIN_STATUS = OrderedDict()
PLUGIN_STATUS["conflict_untracked"] = (
    lambda plugin: _create_conflict(plugin),
    dict(
        conflict_untracked=[
            (u"/en/tutorial/subdir3/subsubdir/example5.po",
             "/non_gnu_style/locales/en/subsubdir/example5.po")]))
PLUGIN_STATUS["fs_unmatched"] = (
    lambda plugin: _edit_file(plugin, "foo.po"), {})
PLUGIN_STATUS["fs_untracked"] = (
    lambda plugin: _edit_file(
        plugin, "non_gnu_style/locales/en/subsubdir/example5.po"),
    dict(
        fs_untracked=[
            (u"/en/tutorial/subdir3/subsubdir/example5.po",
             "/non_gnu_style/locales/en/subsubdir/example5.po")]))
PLUGIN_STATUS["pootle_untracked"] = (
    lambda plugin: _setup_store(
        plugin, path="subdir3/subsubdir/example5.po"),
    dict(
        pootle_untracked=[
            (u"/en/tutorial/subdir3/subsubdir/example5.po",
             "/non_gnu_style/locales/en/subsubdir/example5.po")]))
PLUGIN_STATUS["fs_added"] = (
    lambda plugin: (
        _edit_file(
            plugin, "non_gnu_style/locales/en/subsubdir/example5.po"),
        plugin.fetch_translations()),
    dict(
        fs_added=[
            (u"/en/tutorial/subdir3/subsubdir/example5.po",
             "/non_gnu_style/locales/en/subsubdir/example5.po")]))
PLUGIN_STATUS["pootle_added"] = (
    lambda plugin: (
        _setup_store(plugin, path="subdir3/subsubdir/example5.po"),
        plugin.add_translations()),
    dict(
        pootle_added=[
            (u"/en/tutorial/subdir3/subsubdir/example5.po",
             "/non_gnu_style/locales/en/subsubdir/example5.po")]))
PLUGIN_STATUS["fs_ahead"] = (
    lambda plugin: (
        _edit_file(
            plugin, "non_gnu_style/locales/en/subsubdir/example4.po"),
        plugin.fetch_translations()),
    dict(
        fs_ahead=[
            (u"/en/tutorial/subdir3/subsubdir/example4.po",
             "/non_gnu_style/locales/en/subsubdir/example4.po")]))
PLUGIN_STATUS["pootle_ahead"] = (
    lambda plugin: (
        _update_store(
            pootle_path="/en/tutorial/subdir3/subsubdir/example4.po"),
        plugin.add_translations()),
    dict(
        pootle_ahead=[
            (u"/en/tutorial/subdir3/subsubdir/example4.po",
             "/non_gnu_style/locales/en/subsubdir/example4.po")]))
PLUGIN_STATUS["fs_removed"] = (
    lambda plugin: _remove_file(
        plugin, "non_gnu_style/locales/en/subsubdir/example4.po"),
    dict(
        fs_removed=[
            (u"/en/tutorial/subdir3/subsubdir/example4.po",
             "/non_gnu_style/locales/en/subsubdir/example4.po")]))
PLUGIN_STATUS["pootle_removed"] = (
    lambda plugin: _remove_store(
        pootle_path="/en/tutorial/subdir3/subsubdir/example4.po"),
    dict(
        pootle_removed=[
            (u"/en/tutorial/subdir3/subsubdir/example4.po",
             "/non_gnu_style/locales/en/subsubdir/example4.po")]))
PLUGIN_STATUS["conflict"] = (
    lambda plugin: (
        _update_store(
            pootle_path="/en/tutorial/subdir3/subsubdir/example4.po"),
        _edit_file(
            plugin, "non_gnu_style/locales/en/subsubdir/example4.po")),
    dict(
        conflict=[
            (u"/en/tutorial/subdir3/subsubdir/example4.po",
             "/non_gnu_style/locales/en/subsubdir/example4.po")]))

PARAMETERS = (
    ("bad_finder_paths", BAD_FINDER_PATHS),
    ("root_paths", ROOT_PATHS),
    ("finder_regexes", FINDER_REGEXES),
    ("files", FILES),
    ("matches", MATCHES),
    ("plugin_status", PLUGIN_STATUS),
    ("conflict_outcomes", CONFLICT))


def pytest_generate_tests(metafunc):
    for name, params in PARAMETERS:
        if name in metafunc.fixturenames:
            metafunc.parametrize(name, params)


def _test_status(plugin, expected):
    status = plugin.status()
    assert status.has_changed is (expected and True or False)
    for k in STATUS_TYPES:
        if k in expected:
            assert expected[k] == [
                (s.pootle_path, s.fs_path)
                for s in status[k]]
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


def _update_store(plugin=None, pootle_path=None):
    from pootle_store.models import Unit, Store
    if pootle_path:
        store = Store.objects.get(pootle_path=pootle_path)
    else:
        # Update the store revision
        store = plugin.stores.first()
    Unit.objects.create(
        unitid="Foo", store=store, index=0, revision=1)


def _remove_store(plugin=None, pootle_path=None):
    from pootle_store.models import Store
    if pootle_path:
        store = Store.objects.get(pootle_path=pootle_path)
    else:
        # Update the store revision
        store = plugin.stores.first()
    # Remove the store
    store.delete()


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

        def get_latest_hash(self):
            return md5(str(datetime.now())).hexdigest()

        def pull(self):
            dir_path = self.local_fs_path
            if not self._pulled:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                shutil.copytree(
                    os.path.abspath(
                        os.path.join(
                            __file__,
                            self.src)),
                    os.path.abspath(dir_path))
            self._pulled = True

    ExamplePlugin.name = name
    ExamplePlugin.src = os.path.abspath(src)
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
    return EXPECTED_FS_STORES

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


@pytest.fixture
def fs_plugin_conflicted(fs_plugin_pulled, system):
    _edit_file(fs_plugin_pulled, "gnu_style/po/en.po")
    _update_store(fs_plugin_pulled)
    return fs_plugin_pulled


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
def fs_plugin_conflict_untracked(tutorial_fs, tmpdir, settings):
    dir_path = str(tmpdir.dirpath())
    _clear_fs(dir_path, tutorial_fs)
    _setup_store(tutorial_fs)
    plugin = _register_plugin(src=_setup_dir(dir_path))
    settings.POOTLE_FS_PATH = dir_path
    return plugin(tutorial_fs)


@pytest.fixture
def finder_matches(matches):
    return [matches] + list(MATCHES[matches])


@pytest.fixture
def finder_root_paths(root_paths):
    return root_paths, ROOT_PATHS[root_paths]


@pytest.fixture
def finder_files(files):
    return files, FILES[files]


@pytest.fixture
def fs_finder(fs_plugin_pulled, finder_files):
    from pootle_fs.finder import TranslationFileFinder
    translation_path, expected = finder_files
    finder = TranslationFileFinder(
        os.path.join(
            fs_plugin_pulled.local_fs_path,
            translation_path))
    expected = [
        (os.path.join(fs_plugin_pulled.local_fs_path,
                      path),
         parsed)
        for path, parsed in expected]
    return finder, expected


@pytest.fixture
def fs_status(fs_plugin_pulled, plugin_status, system):
    return [fs_plugin_pulled] + list(PLUGIN_STATUS[plugin_status])
