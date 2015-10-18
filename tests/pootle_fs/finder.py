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

from pootle_fs.finder import TranslationFileFinder


# Parametrized: ROOT_PATHS
@pytest.mark.django
def test_finder_file_root(finder_root_paths):
    dir_path = "/some/path"
    path, expected = finder_root_paths
    assert (
        TranslationFileFinder(
            os.path.join(dir_path, path)).file_root
        == (
            expected
            and os.path.join(dir_path, expected)
            or dir_path))


# Parametrized: BAD_FINDER_PATHS
@pytest.mark.django
def test_finder_bad_paths(bad_finder_paths):
    dir_path = "/some/path"
    with pytest.raises(ValueError):
        TranslationFileFinder(os.path.join(dir_path, bad_finder_paths))


# Parametrized: FINDER_REGEXES
@pytest.mark.django
def test_finder_regex(finder_regexes):
    dir_path = "/some/path"
    translation_path = os.path.join(dir_path, finder_regexes)
    finder = TranslationFileFinder(translation_path)
    path = translation_path
    for k, v in TranslationFileFinder.path_mapping:
        path = path.replace(k, v)
    path = os.path.splitext(path)
    path = "%s%s" % (path[0], finder._ext_re())
    assert finder.regex.pattern == "%s$" % path


# Parametrized: MATCHES
@pytest.mark.django
def test_finder_match(finder_matches):
    dir_path = "/some/path"
    match_path, not_matching, matching = finder_matches
    finder = TranslationFileFinder(os.path.join(dir_path, match_path))

    for path in not_matching:
        assert not finder.match(
            os.path.join(dir_path, path))
    for path, expected in matching:
        match = finder.match(os.path.join(dir_path, path))
        assert match
        named = match.groupdict()
        for k in ["lang", "directory_path", "filename", "ext"]:
            if k in expected:
                assert named[k].strip("/") == expected[k]
            else:
                assert k not in named
        reverse = finder.reverse_match(
            named['lang'],
            named.get('filename', os.path.splitext(os.path.basename(path))[0]),
            named['ext'],
            directory_path=named.get('directory_path'))

        assert os.path.join(dir_path, path) == reverse


# Parametrized: FILES
@pytest.mark.django
def test_finder_find(fs_finder):
    finder, expected = fs_finder
    assert sorted(expected) == sorted(f for f in finder.find())
