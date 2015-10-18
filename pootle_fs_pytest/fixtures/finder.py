# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict
import os

import pytest

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
    ["en.po", "foo/bar/en.po"],
    [("po/en.po", dict(lang="en", ext="po"))])
MATCHES["po-<filename>/<lang>.po"] = (
    ["en.po", "po/en.po"],
    [("po-foo/en.po", dict(lang="en", filename="foo", ext="po"))])
MATCHES["po/<filename>-<lang>.po"] = (
    ["en.po", "po/en.po"],
    [("po/foo-en.po", dict(lang="en", filename="foo", ext="po"))])
MATCHES["<lang>/<directory_path>/<filename>.po"] = (
    ["foo.po"],
    [("en/foo.po",
      dict(lang="en", directory_path="", filename="foo", ext="po")),
     ("en/foo.pot",
      dict(lang="en", directory_path="", filename="foo", ext="pot")),
     ("en/bar/baz/foo.po",
      dict(lang="en", directory_path="bar/baz", filename="foo", ext="po"))])
MATCHES["<directory_path>/<lang>/<filename>.po"] = (
    ["foo.po", "en/foo.poo"],
    [("en/foo.po",
      dict(lang="en", directory_path="", filename="foo", ext="po")),
     ("en/foo.pot",
      dict(lang="en", directory_path="", filename="foo", ext="pot")),
     ("bar/baz/en/foo.po",
      dict(lang="en", directory_path="bar/baz", filename="foo", ext="po"))])

FINDER_REGEXES = [
    "<lang>.po",
    "<lang>/<filename>.po",
    "<directory_path>/<lang>.po",
    "<lang><directory_path>/<filename>.po"]

FILES = OrderedDict()
FILES["gnu_style/po/<lang>.po"] = (
    ("gnu_style/po/zu.po",
     dict(lang="zu",
          ext="po",
          filename="zu",
          directory_path="")),
    ("gnu_style/po/en.po",
     dict(lang="en",
          ext="po",
          filename="en",
          directory_path="")))
FILES["gnu_style_named_files/po/<filename>-<lang>.po"] = (
    ("gnu_style_named_files/po/example1-en.po",
     dict(lang="en",
          filename="example1",
          ext="po",
          directory_path="")),
    ("gnu_style_named_files/po/example1-zu.po",
     dict(lang="zu",
          filename="example1",
          ext="po",
          directory_path="")),
    ("gnu_style_named_files/po/example2-en.po",
     dict(lang="en",
          filename="example2",
          ext="po",
          directory_path="")),
    ("gnu_style_named_files/po/example2-zu.po",
     dict(lang="zu",
          filename="example2",
          ext="po",
          directory_path="")))
FILES["gnu_style_named_folders/po-<filename>/<lang>.po"] = (
    ("gnu_style_named_folders/po-example1/en.po",
     dict(lang="en",
          filename="example1",
          ext="po",
          directory_path="")),
    ("gnu_style_named_folders/po-example1/zu.po",
     dict(lang="zu",
          filename="example1",
          ext="po",
          directory_path="")),
    ("gnu_style_named_folders/po-example2/en.po",
     dict(lang="en",
          filename="example2",
          ext="po",
          directory_path="")),
    ("gnu_style_named_folders/po-example2/zu.po",
     dict(lang="zu",
          filename="example2",
          ext="po",
          directory_path="")))
FILES["non_gnu_style/locales/<lang>/<directory_path>/<filename>.po"] = (
    ("non_gnu_style/locales/en/example1.po",
     dict(lang="en",
          filename="example1",
          ext="po",
          directory_path="")),
    ("non_gnu_style/locales/zu/example1.po",
     dict(lang="zu",
          filename="example1",
          ext="po",
          directory_path="")),
    ("non_gnu_style/locales/en/example2.po",
     dict(lang="en",
          filename="example2",
          ext="po",
          directory_path="")),
    ("non_gnu_style/locales/zu/example2.po",
     dict(lang="zu",
          filename="example2",
          ext="po",
          directory_path="")),
    ("non_gnu_style/locales/en/subsubdir/example3.po",
     dict(lang="en",
          filename="example3",
          ext="po",
          directory_path="subsubdir")),
    ("non_gnu_style/locales/zu/subsubdir/example3.po",
     dict(lang="zu",
          filename="example3",
          ext="po",
          directory_path="subsubdir")),
    ("non_gnu_style/locales/en/subsubdir/example4.po",
     dict(lang="en",
          filename="example4",
          ext="po",
          directory_path="subsubdir")),
    ("non_gnu_style/locales/zu/subsubdir/example4.po",
     dict(lang="zu",
          filename="example4",
          ext="po",
          directory_path="subsubdir")))


@pytest.fixture
def finder_files(files):
    return files, FILES[files]


@pytest.fixture
def fs_finder(fs_plugin_synced, finder_files):
    from pootle_fs.finder import TranslationFileFinder
    translation_path, expected = finder_files
    finder = TranslationFileFinder(
        os.path.join(
            fs_plugin_synced.local_fs_path,
            translation_path))
    expected = [
        (os.path.join(fs_plugin_synced.local_fs_path,
                      path),
         parsed)
        for path, parsed in expected]
    return finder, expected


@pytest.fixture
def finder_matches(matches):
    return [matches] + list(MATCHES[matches])


@pytest.fixture
def finder_root_paths(root_paths):
    return root_paths, ROOT_PATHS[root_paths]
