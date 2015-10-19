#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_fs.management.commands import SubCommand


class ProjectInfoCommand(SubCommand):
    help = "List FS translations files managed by Pootle."

    def handle(self, project_code, *args, **options):
        fs = self.get_fs(project_code)
        self.stdout.write("Self.Project: %s" % self.project.code)
        self.stdout.write("type: %s" % fs.fs_type)
        self.stdout.write("URL: %s" % fs.url)
        self.stdout.write("enabled: %s" % fs.enabled)
        self.stdout.write("latest commit: %s" % fs.plugin.get_latest_hash())
        self.stdout.write("fetch frequency: %s" % fs.fetch_frequency)
        self.stdout.write("push frequency: %s" % fs.push_frequency)
