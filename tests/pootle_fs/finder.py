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


@pytest.mark.django
def test_finder_file_root():
    dir_path = "/some/path"

    assert (
        TranslationFileFinder(
            os.path.join(dir_path, "<lang>.po")).file_root
        == dir_path)

    assert (
        TranslationFileFinder(
            os.path.join(dir_path, "foo/<lang>.po")).file_root
        == os.path.join(dir_path, "foo"))

    assert (
        TranslationFileFinder(
            os.path.join(
                dir_path,
                "foo/bar/baz-<filename>-<lang>.po")).file_root
        == os.path.join(dir_path, "foo/bar"))


@pytest.mark.django
def test_finder_bad_paths():
    dir_path = "/some/path"

    # missing <lang>
    with pytest.raises(ValueError):
        TranslationFileFinder(os.path.join(dir_path, "lang/foo.po"))

    # invalid <foo> tag
    with pytest.raises(ValueError):
        TranslationFileFinder(os.path.join(dir_path, "<lang>/<foo>.po"))

    # "../foo/bar"
    with pytest.raises(ValueError):
        TranslationFileFinder(os.path.join(dir_path, "../<lang>/foo.po"))

    # "foo/../bar"
    with pytest.raises(ValueError):
        TranslationFileFinder(os.path.join(dir_path, "<lang>/../foo.po"))

    # "foo/bar/.."
    with pytest.raises(ValueError):
        TranslationFileFinder(os.path.join(dir_path, "<lang>/.."))

    # "foo/@<lang>/bar.po"
    with pytest.raises(ValueError):
        TranslationFileFinder(os.path.join(dir_path, "foo/@<lang>/bar.po"))


@pytest.mark.django
def test_finder_regex():
    dir_path = "/some/path"

    translation_path = os.path.join(dir_path, "<lang>.po")
    finder = TranslationFileFinder(translation_path)
    assert(
        finder.regex.pattern
        == ("%s$"
            % (translation_path.replace(".", "\.")
                               .replace("<lang>", "(?P<lang>[\w]*)"))))

    translation_path = os.path.join(dir_path, "<lang>/<filename>.po")
    finder = TranslationFileFinder(translation_path)
    assert(
        finder.regex.pattern
        == ("%s$"
            % (translation_path.replace(".", "\.")
                               .replace("<lang>", "(?P<lang>[\w]*)")
                               .replace("<filename>", "(?P<filename>[\w]*)"))))

    translation_path = os.path.join(dir_path, "<directory_path>/<lang>.po")
    finder = TranslationFileFinder(translation_path)
    assert(
        finder.regex.pattern
        == ("%s$"
            % (translation_path.replace(".", "\.")
                               .replace("<directory_path>",
                                        "(?P<directory_path>[\w\/]*?)")
                               .replace("<lang>", "(?P<lang>[\w]*)"))))

    translation_path = os.path.join(
        dir_path, "<lang><directory_path>/<filename>.po")
    finder = TranslationFileFinder(translation_path)
    assert(
        finder.regex.pattern
        == ("%s$"
            % (translation_path.replace(".", "\.")
                               .replace("<directory_path>",
                                        "(?P<directory_path>[\w\/]*?)")
                               .replace("<lang>", "(?P<lang>[\w]*)")
                               .replace("<filename>", "(?P<filename>[\w]*)"))))


@pytest.mark.django
def test_finder_regex_match_gnu():
    dir_path = "/some/path"

    translation_path = os.path.join(
        dir_path, "po/<lang>.po")
    finder = TranslationFileFinder(translation_path)

    match = finder.match(os.path.join(dir_path, "en.po"))
    assert not match

    match = finder.match(os.path.join(dir_path, "foo/bar/en.po"))
    assert not match

    match = finder.match(os.path.join(dir_path, "po/en.po"))
    assert match
    named = match.groupdict()
    assert named["lang"] == "en"
    assert "directory_path" not in named
    assert "filename" not in named


@pytest.mark.django
def test_finder_regex_match_gnu_named_folders():
    dir_path = "/some/path"

    translation_path = os.path.join(
        dir_path, "po-<filename>/<lang>.po")
    finder = TranslationFileFinder(translation_path)

    match = finder.match(os.path.join(dir_path, "en.po"))
    assert not match

    match = finder.match(os.path.join(dir_path, "po/en.po"))
    assert not match

    match = finder.match(os.path.join(dir_path, "po-foo/en.po"))
    assert match

    named = match.groupdict()
    assert named["lang"] == "en"
    assert "directory_path" not in named
    assert named["filename"] == "foo"


@pytest.mark.django
def test_finder_regex_match_gnu_named_files():
    dir_path = "/some/path"

    translation_path = os.path.join(
        dir_path, "po/<filename>-<lang>.po")
    finder = TranslationFileFinder(translation_path)

    match = finder.match(os.path.join(dir_path, "en.po"))
    assert not match

    match = finder.match(os.path.join(dir_path, "po/en.po"))
    assert not match

    match = finder.match(os.path.join(dir_path, "po/foo-en.po"))
    assert match

    named = match.groupdict()
    assert named["lang"] == "en"
    assert "directory_path" not in named
    assert named["filename"] == "foo"


@pytest.mark.django
def test_finder_regex_match_non_gnu():
    dir_path = "/some/path"

    translation_path = os.path.join(
        dir_path, "<lang><directory_path>/<filename>.po")
    finder = TranslationFileFinder(translation_path)

    match = finder.match(os.path.join(dir_path, "foo.po"))
    assert not match

    match = finder.match(os.path.join(dir_path, "en/foo.po"))
    assert match
    named = match.groupdict()
    assert named["lang"] == "en"
    assert named["directory_path"] == ""
    assert named["filename"] == "foo"

    match = finder.match(os.path.join(dir_path, "en/bar/baz/foo.po"))
    assert match
    named = match.groupdict()
    assert named["lang"] == "en"
    assert named["directory_path"].strip("/") == "bar/baz"
    assert named["filename"] == "foo"


@pytest.mark.django
def test_finder_regex_match_non_gnu_reversed():
    dir_path = "/some/path"
    translation_path = os.path.join(
        dir_path, "<directory_path><lang>/<filename>.po")
    finder = TranslationFileFinder(translation_path)

    match = finder.match(os.path.join(dir_path, "foo.po"))
    assert not match

    match = finder.match(os.path.join(dir_path, "en/foo.po"))
    assert match
    named = match.groupdict()
    assert named["lang"] == "en"
    assert named["directory_path"] == ""
    assert named["filename"] == "foo"

    match = finder.match(os.path.join(dir_path, "bar/baz/en/foo.po"))
    assert match
    named = match.groupdict()
    assert named["lang"] == "en"
    assert named["directory_path"].strip("/") == "bar/baz"
    assert named["filename"] == "foo"


@pytest.mark.django
def test_finder_find_gnu_style(tmp_pootle_fs):
    dir_path = os.path.join(str(tmp_pootle_fs.dirpath()), "example_fs")

    translation_path = os.path.join(
        dir_path, "gnu_style/po/<lang>.po")
    finder = TranslationFileFinder(translation_path)

    expected = (
        (os.path.join(dir_path, "gnu_style/po/zu.po"),
         dict(lang="zu",
              directory_path="")),
        (os.path.join(dir_path, "gnu_style/po/en.po"),
         dict(lang="en",
              directory_path="")))

    assert sorted(expected) == sorted(f for f in finder.find())


@pytest.mark.django
def test_finder_find_gnu_style_named_folders(tmp_pootle_fs):
    dir_path = os.path.join(str(tmp_pootle_fs.dirpath()), "example_fs")
    finder = TranslationFileFinder(os.path.join(
        dir_path, "gnu_style_named_folders/po-<filename>/<lang>.po"))
    expected = (
        (os.path.join(dir_path, "gnu_style_named_folders/po-example1/en.po"),
         dict(lang="en",
              filename="example1",
              directory_path="")),
        (os.path.join(dir_path, "gnu_style_named_folders/po-example1/zu.po"),
         dict(lang="zu",
              filename="example1",
              directory_path="")),
        (os.path.join(dir_path, "gnu_style_named_folders/po-example2/en.po"),
         dict(lang="en",
              filename="example2",
              directory_path="")),
        (os.path.join(dir_path, "gnu_style_named_folders/po-example2/zu.po"),
         dict(lang="zu",
              filename="example2",
              directory_path="")))
    assert sorted(expected) == sorted(f for f in finder.find())


@pytest.mark.django
def test_finder_find_gnu_style_named_files(tmp_pootle_fs):
    dir_path = os.path.join(str(tmp_pootle_fs.dirpath()), "example_fs")
    finder = TranslationFileFinder(os.path.join(
        dir_path, "gnu_style_named_files/po/<filename>-<lang>.po"))
    expected = (
        (os.path.join(dir_path, "gnu_style_named_files/po/example1-en.po"),
         dict(lang="en",
              filename="example1",
              directory_path="")),
        (os.path.join(dir_path, "gnu_style_named_files/po/example1-zu.po"),
         dict(lang="zu",
              filename="example1",
              directory_path="")),
        (os.path.join(dir_path, "gnu_style_named_files/po/example2-en.po"),
         dict(lang="en",
              filename="example2",
              directory_path="")),
        (os.path.join(dir_path, "gnu_style_named_files/po/example2-zu.po"),
         dict(lang="zu",
              filename="example2",
              directory_path="")))
    assert sorted(expected) == sorted(f for f in finder.find())


@pytest.mark.django
def test_finder_find_non_gnu(tmp_pootle_fs):
    dir_path = os.path.join(str(tmp_pootle_fs.dirpath()), "example_fs")
    finder = TranslationFileFinder(
        os.path.join(
            dir_path,
            "non_gnu_style/locales/<lang><directory_path>/<filename>.po"))
    expected = (
        (os.path.join(dir_path,
                      "non_gnu_style/locales/en/example1.po"),
         dict(lang="en",
              filename="example1",
              directory_path="")),
        (os.path.join(dir_path,
                      "non_gnu_style/locales/zu/example1.po"),
         dict(lang="zu",
              filename="example1",
              directory_path="")),
        (os.path.join(dir_path,
                      "non_gnu_style/locales/en/example2.po"),
         dict(lang="en",
              filename="example2",
              directory_path="")),
        (os.path.join(dir_path, "non_gnu_style/locales/zu/example2.po"),
         dict(lang="zu",
              filename="example2",
              directory_path="")),
        (os.path.join(dir_path,
                      "non_gnu_style/locales/en/subsubdir/example3.po"),
         dict(lang="en",
              filename="example3",
              directory_path="subsubdir")),
        (os.path.join(dir_path,
                      "non_gnu_style/locales/zu/subsubdir/example3.po"),
         dict(lang="zu",
              filename="example3",
              directory_path="subsubdir")),
        (os.path.join(dir_path,
                      "non_gnu_style/locales/en/subsubdir/example4.po"),
         dict(lang="en",
              filename="example4",
              directory_path="subsubdir")),
        (os.path.join(dir_path,
                      "non_gnu_style/locales/zu/subsubdir/example4.po"),
         dict(lang="zu",
              filename="example4",
              directory_path="subsubdir")))
    assert sorted(expected) == sorted(f for f in finder.find())
