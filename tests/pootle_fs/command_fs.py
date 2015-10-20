#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import io
import os

import pytest

from django.core.management import call_command, CommandError

from pootle_fs.models import ProjectFS


@pytest.mark.django
def test_command_fs(fs_plugin, capsys):
    call_command("fs")
    out, err = capsys.readouterr()
    plugins = [
        project_fs.plugin for project_fs
        in ProjectFS.objects.all()]
    expected = (
        "%s\n"
        % '\n'.join(
            ["%s\t%s" % (plugin.project.code, plugin.fs.url)
             for plugin in plugins]))
    assert out == expected


@pytest.mark.django
def test_command_fs_info(fs_plugin, capsys):
    call_command("fs", fs_plugin.project.code)
    out, err = capsys.readouterr()
    # TODO


def _test_status(status, out):
    expected = ""

    if not status.has_changed:
        assert out == "Everything up-to-date\n"
        return

    def _status_line(fs_status):
        fs_exists_status = [
            "fs_untracked", "fs_added", "fs_ahead",
            "pootle_ahead", "pootle_removed",
            "conflict", "conflict_untracked",
            "merge_fs", "merge_pootle"]
        store_exists_status = [
            "pootle_untracked", "pootle_added", "pootle_ahead",
            "fs_ahead", "fs_removed",
            "conflict", "conflict_untracked",
            "merge_fs", "merge_pootle"]
        fs_exists = (
            fs_status.status in fs_exists_status
            or (fs_status.status == "to_remove"
                and fs_status.store_fs.file.exists))
        store_exists = (
            fs_status.status in store_exists_status
            or (fs_status.status == "to_remove"
                and not fs_status.store_fs.file.exists))

        if fs_exists:
            fs_path = fs_status.fs_path
        else:
            fs_path = "(%s)" % fs_status.fs_path
        if store_exists:
            pootle_path = fs_status.pootle_path
        else:
            pootle_path = "(%s)" % fs_status.pootle_path
        return (
            "  %s\n   <-->  %s"
            % (pootle_path, fs_path))

    for k in status:
        title = status.get_status_title(k)
        description = status.get_status_description(k)
        expected += (
            "%s\n%s\n%s\n\n%s\n\n"
            % (title,
               "-" * len(title),
               description,
               "\n".join([_status_line(fs_status)
                          for fs_status in status[k]])))
    assert out == expected


def _test_response(response, out, err):
    expected = ""

    if response is None:
        raise Exception

    def _response_line(action):

        fs_exists_actions = [
            "pulled_to_pootle", "pushed_to_fs", "fetched_from_fs",
            "staged_for_merge_fs", "staged_for_merge_pootle",
            "merged_from_fs", "merged_from_pootle"]

        store_exists_actions = [
            "pulled_to_pootle", "pushed_to_fs", "added_from_pootle",
            "staged_for_merge_fs", "staged_for_merge_pootle",
            "merged_from_fs", "merged_from_pootle"]

        file_exists = (
            action.action_type in fs_exists_actions
            or (action.original_status.status
                in ["conflict", "conflict_untracked"])
            or (action.action_type == "staged_for_removal"
                and (action.original_status.status
                     in ["fs_untracked", "pootle_removed"])))

        store_exists = (
            action.action_type in store_exists_actions
            or (action.original_status.status
                in ["conflict", "conflict_untracked"])
            or (action.action_type == "staged_for_removal"
                and (action.original_status.status
                     in ["pootle_untracked", "fs_removed"])))

        if file_exists:
            fs_path = action.fs_path
        else:
            fs_path = "(%s)" % action.fs_path
        if store_exists:
            pootle_path = action.pootle_path
        else:
            pootle_path = "(%s)" % action.pootle_path

        return (
            "  %s\n   <-->  %s"
            % (pootle_path, fs_path))

    if not response.made_changes:
        assert out == "No changes made\n"
        return

    for k in response:
        title = response.get_action_title(k)
        description = response.get_action_description(k)
        expected += (
            "%s\n%s\n%s\n\n%s\n\n"
            % (title,
               "-" * len(title),
               description,
               "\n".join([_response_line(action)
                          for action in response[k]])))
    assert out == expected


@pytest.mark.django
def test_command_status_fetch(fs_plugin_suite, capsys):
    plugin = fs_plugin_suite
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()
    _test_status(plugin.status(), out)

    plugin.fetch_translations()
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()
    _test_status(plugin.status(), out)

    plugin.fetch_translations(force=True)
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()
    _test_status(plugin.status(), out)

    plugin.sync_translations()
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()

    _test_status(plugin.status(), out)


@pytest.mark.django
def test_command_status_add(fs_plugin_suite, capsys):
    plugin = fs_plugin_suite
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()
    _test_status(plugin.status(), out)

    plugin.add_translations()
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()
    _test_status(plugin.status(), out)

    plugin.add_translations(force=True)
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()
    _test_status(plugin.status(), out)

    plugin.sync_translations()
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()

    _test_status(plugin.status(), out)


@pytest.mark.django
def test_command_status_merge_fs(fs_plugin_suite, capsys):
    plugin = fs_plugin_suite
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()
    _test_status(plugin.status(), out)

    plugin.merge_translations()
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()
    _test_status(plugin.status(), out)

    plugin.sync_translations()
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()

    _test_status(plugin.status(), out)


@pytest.mark.django
def test_command_status_merge_pootle(fs_plugin_suite, capsys):
    plugin = fs_plugin_suite
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()
    _test_status(plugin.status(), out)

    plugin.merge_translations(pootle_wins=True)
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()
    _test_status(plugin.status(), out)

    plugin.sync_translations()
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()

    _test_status(plugin.status(), out)


@pytest.mark.django
def test_command_status_rm(fs_plugin_suite, capsys):
    plugin = fs_plugin_suite
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()
    _test_status(plugin.status(), out)

    plugin.rm_translations()
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()
    _test_status(plugin.status(), out)

    plugin.sync_translations()
    call_command("fs", plugin.project.code, "status")
    out, err = capsys.readouterr()

    _test_status(plugin.status(), out)


@pytest.mark.django
def test_command_config(fs_plugin_suite, capsys):
    plugin = fs_plugin_suite
    call_command("fs", plugin.project.code, "config")
    out, err = capsys.readouterr()
    with open(os.path.join(plugin.fs.url, ".pootle.ini")) as f:
        assert out.strip() == f.read().strip()
    saved_conf = io.BytesIO()
    config = plugin.read_config()
    config.set("default", "some", "setting")
    config.write(saved_conf)
    saved_conf.seek(0)
    saved_conf = saved_conf.read().strip()
    config.write(
        open(
            os.path.join(plugin.fs.url, ".pootle.ini"), "w"))
    call_command("fs", plugin.project.code, "config", update=True)
    new_out, err = capsys.readouterr()
    assert new_out == "Config updated\n"
    call_command("fs", plugin.project.code, "config")
    out, err = capsys.readouterr()
    assert out.strip() == saved_conf


@pytest.mark.django
def test_command_set_fs(fs_plugin, capsys):
    plugin = fs_plugin

    plugin.pull()
    assert plugin.is_cloned

    with pytest.raises(CommandError):
        call_command("fs", "tutorial", "set_fs")

    with pytest.raises(CommandError):
        call_command("fs", "tutorial", "set_fs", "foo")

    with pytest.raises(CommandError):
        call_command("fs", "tutorial", "set_fs", "foo", "bar")

    # "example" plugin is registered so this works...
    call_command("fs", "tutorial", "set_fs", "example", "bar")

    # at this point the plugin.fs is stale
    assert plugin.fs.url != "bar"

    plugin.reload()

    # but now the url should be set
    assert plugin.fs.url == "bar"

    # changing the fs_type/url results in the local_fs being deleted
    assert plugin.is_cloned is False


@pytest.mark.django
def test_command_merge_translations_fs(fs_plugin_suite, capsys):
    _test_response(
        call_command(
            "fs", fs_plugin_suite.project.code,
            "merge_translations"),
        *capsys.readouterr())

    _test_response(
        call_command(
            "fs", fs_plugin_suite.project.code,
            "sync_translations"),
        *capsys.readouterr())


@pytest.mark.django
def test_command_merge_translations_pootle(fs_plugin_suite, capsys):
    _test_response(
        call_command(
            "fs", fs_plugin_suite.project.code,
            "merge_translations", pootle_wins=True),
        *capsys.readouterr())

    _test_response(
        call_command(
            "fs", fs_plugin_suite.project.code,
            "sync_translations"),
        *capsys.readouterr())


@pytest.mark.django
def test_command_rm_translations(fs_plugin_suite, capsys):
    _test_response(
        call_command(
            "fs", fs_plugin_suite.project.code,
            "rm_translations"),
        *capsys.readouterr())

    _test_response(
        call_command(
            "fs", fs_plugin_suite.project.code,
            "sync_translations"),
        *capsys.readouterr())


@pytest.mark.django
def test_command_add_translations(fs_plugin_suite, capsys):
    _test_response(
        call_command(
            "fs", fs_plugin_suite.project.code,
            "add_translations"),
        *capsys.readouterr())

    _test_response(
        call_command(
            "fs", fs_plugin_suite.project.code,
            "sync_translations"),
        *capsys.readouterr())


@pytest.mark.django
def test_command_add_translations_force(fs_plugin_suite, capsys):
    _test_response(
        call_command(
            "fs", fs_plugin_suite.project.code,
            "add_translations", force=True),
        *capsys.readouterr())

    _test_response(
        call_command(
            "fs", fs_plugin_suite.project.code,
            "sync_translations"),
        *capsys.readouterr())


@pytest.mark.django
def test_command_fetch_translations(fs_plugin_suite, capsys):
    _test_response(
        call_command(
            "fs", fs_plugin_suite.project.code,
            "fetch_translations"),
        *capsys.readouterr())

    _test_response(
        call_command(
            "fs", fs_plugin_suite.project.code,
            "sync_translations"),
        *capsys.readouterr())


@pytest.mark.django
def test_command_fetch_translations_force(fs_plugin_suite, capsys):
    _test_response(
        call_command(
            "fs", fs_plugin_suite.project.code,
            "fetch_translations", force=True),
        *capsys.readouterr())

    _test_response(
        call_command(
            "fs", fs_plugin_suite.project.code,
            "sync_translations"),
        *capsys.readouterr())


@pytest.mark.django
def test_command_fs_no_projects(tutorial, capsys):
    call_command("fs")
    out, err = capsys.readouterr()
    assert out == "No projects configured\n"


@pytest.mark.django
def test_command_fs_bad_project(fs_plugin_suite, capsys):
    with pytest.raises(CommandError):
        call_command(
            "fs", "BAD_PROJECT_CODE")

    with pytest.raises(CommandError):
        call_command(
            "fs", "tutorial", "BAD_SUBCOMMAND")


@pytest.mark.django
def test_command_fs_argv_subcommands(fs_plugin_suite, capsys):
    from pootle_fs.management.commands.fs import Command
    command = Command().run_from_argv

    with pytest.raises(SystemExit):
        command(
            ["pootle", "fs", "BAD_PROJECT_CODE"])

    with pytest.raises(SystemExit):
        command(
            ["pootle", "fs", "tutorial", "BAD_SUBCOMMAND"])

    out, err = capsys.readouterr()
    command(["pootle", "fs"])
    out, err = capsys.readouterr()
    plugins = [
        project_fs.plugin for project_fs
        in ProjectFS.objects.all()]
    expected = (
        "%s\n"
        % '\n'.join(
            ["%s\t%s" % (plugin.project.code, plugin.fs.url)
             for plugin in plugins]))
    assert out == expected
