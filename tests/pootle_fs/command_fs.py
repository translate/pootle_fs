#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command

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


@pytest.mark.django
def test_command_fs_status(fs_plugin, capsys):
    call_command("fs", fs_plugin.project.code, "status")
    out, err = capsys.readouterr()
    # TODO
