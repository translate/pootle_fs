# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

import pytest

from .utils import (
    _create_conflict, _edit_file, _remove_file, _remove_store, _setup_store,
    _update_store)


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


@pytest.fixture
def fs_status(fs_plugin_pulled, plugin_status, system):
    return [fs_plugin_pulled] + list(PLUGIN_STATUS[plugin_status])
