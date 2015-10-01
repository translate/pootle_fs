#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import pytest
import shutil
from md5 import md5


EXAMPLE_FS = os.path.join(__file__, "../../data/fs/example_fs")


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
def example_plugin(tutorial_fs, tmpdir, settings):
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
        (u'/en/tutorial/subdir1/example1',
         '/gnu_style_named_folders/po-example1/en.po'),
        (u'/en/tutorial/subdir1/example2',
         '/gnu_style_named_folders/po-example2/en.po'),
        (u'/en/tutorial/subdir2/example1',
         '/gnu_style_named_files/po/example1-en.po'),
        (u'/en/tutorial/subdir2/example2',
         '/gnu_style_named_files/po/example2-en.po'),
        (u'/en/tutorial/subdir3/example1',
         '/non_gnu_style/locales/en/example1.po'),
        (u'/en/tutorial/subdir3/example2',
         '/non_gnu_style/locales/en/example2.po'),
        (u'/en/tutorial/subdir3/subsubdir/example3',
         '/non_gnu_style/locales/en/subsubdir/example3.po'),
        (u'/en/tutorial/subdir3/subsubdir/example4',
         '/non_gnu_style/locales/en/subsubdir/example4.po'),
        (u'/zu/tutorial/zu.po',
         '/gnu_style/po/zu.po'),
        (u'/zu/tutorial/subdir1/example1',
         '/gnu_style_named_folders/po-example1/zu.po'),
        (u'/zu/tutorial/subdir1/example2',
         '/gnu_style_named_folders/po-example2/zu.po'),
        (u'/zu/tutorial/subdir2/example1',
         '/gnu_style_named_files/po/example1-zu.po'),
        (u'/zu/tutorial/subdir2/example2',
         '/gnu_style_named_files/po/example2-zu.po'),
        (u'/zu/tutorial/subdir3/example1',
         '/non_gnu_style/locales/zu/example1.po'),
        (u'/zu/tutorial/subdir3/example2',
         '/non_gnu_style/locales/zu/example2.po'),
        (u'/zu/tutorial/subdir3/subsubdir/example3',
         '/non_gnu_style/locales/zu/subsubdir/example3.po'),
        (u'/zu/tutorial/subdir3/subsubdir/example4',
         '/non_gnu_style/locales/zu/subsubdir/example4.po')]
