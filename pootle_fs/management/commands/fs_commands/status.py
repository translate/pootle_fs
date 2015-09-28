#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_fs.models import ProjectFS

from pootle_fs.management.commands import SubCommand


class StatusCommand(SubCommand):
    help = "Status of fs repositories."

    def handle(self, project, *args, **options):
        try:
            fs = project.fs.get()
        except ProjectFS.DoesNotExist:
            fs = None
            return
        status = fs.status()
        synced = (
            not status['CONFLICT']
            and not status['POOTLE_AHEAD']
            and not status['POOTLE_ADDED']
            and not status['FS_ADDED']
            and not status['FS_AHEAD'])
        if synced:
            self.stdout.write("Everything up-to-date")
            return
        if status["CONFLICT"]:
            self.stdout.write("Both changed:")
            for repo_file in status["CONFLICT"]:
                self.stdout.write(repo_file)
        if status["POOTLE_ADDED"]:
            for store in status["POOTLE_ADDED"]:
                self.stdout.write(
                    " %-50s %-50s %-20s\n"
                    % ("", store.pootle_path,
                       "Pootle added: %s" % store.get_max_unit_revision()))
        if status["POOTLE_AHEAD"]:
            self.stdout.write("Pootle changed:")
            for repo_file in status["POOTLE_AHEAD"]:
                self.stdout.write(repo_file)
        if status["FS_ADDED"]:
            for store_fs in status["FS_ADDED"]:
                self.stdout.write(
                    " %-50s %-50s %-10s\n"
                    % (store_fs.path,
                       store_fs.store.pootle_path,
                       "FS added: %s"
                       % store_fs.file.latest_hash[:8]))
        if status["FS_AHEAD"]:
            for store_fs in status["FS_AHEAD"]:
                self.stdout.write(
                    " %-50s %-50s %-20s\n"
                    % (store_fs.path,
                       store_fs.store.pootle_path,
                       "FS updated: %s...%s"
                       % (store_fs.last_sync_hash[:8],
                          store_fs.file.latest_hash[:8])))
            self.stdout.write("\n")
