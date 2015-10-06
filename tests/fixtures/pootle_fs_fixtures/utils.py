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
import shutil


EXAMPLE_FS = os.path.join(__file__, "../../../data/fs/example_fs")

STATUS_TYPES = [
    "pootle_ahead", "pootle_added", "pootle_untracked", "pootle_removed",
    "fs_ahead", "fs_added", "fs_untracked", "fs_removed",
    "conflict", "conflict_untracked"]

po_config = """
[default]
translation_path = po/<lang>.po
"""


def _create_conflict(plugin):
    _setup_store(
        plugin,
        path="subdir3/subsubdir/example5.po")
    _edit_file(
        plugin,
        "non_gnu_style/locales/en/subsubdir/example5.po")


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
    dir_name = os.path.dirname(po_file)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
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
    unit = Unit.objects.create(
        unitid="Foo",
        source="Foo",
        store=store,
        index=0,
        revision=store.get_max_unit_revision() or 1)
    unit.target = "Bar"
    unit.save()


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
