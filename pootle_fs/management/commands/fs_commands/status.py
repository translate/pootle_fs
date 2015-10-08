#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from optparse import make_option

from pootle_fs.management.commands import TranslationsSubCommand
from pootle_fs.status import FS_STATUS


class StatusCommand(TranslationsSubCommand):
    help = "Status of fs repositories."
    __status__ = None

    shared_option_list = (
        make_option('-t', '--type', action='append', dest='status_type',
                    help='Status type'),
        )
    option_list = TranslationsSubCommand.option_list + shared_option_list

    @property
    def status(self):
        if not self.__status__:
            self.__status__ = self.plugin.status(
                fs_path=self.fs_path, pootle_path=self.pootle_path)
        return self.__status__

    def handle_status(self, status_type):
        title = self.status.get_status_title(status_type)
        self.stdout.write(title, self.style.HTTP_INFO)
        self.stdout.write("-" * len(title))
        self.stdout.write(self.status.get_status_description(status_type))
        self.stdout.write("")
        handler = getattr(self, "handle_%s" % status_type, None)
        if handler:
            handler()
        else:
            for status in self.status[status_type]:
                self.stdout.write("  %s" % status.pootle_path)
                self.stdout.write("   <-->  %s" % status.fs_path)
        self.stdout.write("")

    def handle_conflict(self):
        for status in self.status["conflict"]:
            self.stdout.write(
                "  %s" % status.pootle_path, self.style.FS_CONFLICT)
            self.stdout.write("   <-->  ", ending="")
            self.stdout.write("%s" % status.fs_path, self.style.FS_CONFLICT)

    def handle_conflict_untracked(self):
        for status in self.status["conflict_untracked"]:
            self.stdout.write(
                "  %s" % status.pootle_path, self.style.FS_CONFLICT)
            self.stdout.write("   <-->  ", ending="")
            self.stdout.write("%s" % status.fs_path, self.style.FS_CONFLICT)

    def handle_fs_untracked(self):
        for status in self.status["fs_untracked"]:
            self.stdout.write(
                "  (%s)" % status.pootle_path,
                self.style.FS_MISSING)
            self.stdout.write("   <-->  ", ending="")
            self.stdout.write("%s" % status.fs_path, self.style.FS_UNTRACKED)

    def handle_fs_added(self):
        for status in self.status["fs_added"]:
            self.stdout.write(
                "  (%s)" % status.pootle_path,
                self.style.FS_MISSING)
            self.stdout.write("   <-->  ", ending="")
            self.stdout.write("%s" % status.fs_path, self.style.FS_ADDED)

    def handle_fs_ahead(self):
        for status in self.status["fs_ahead"]:
            self.stdout.write(
                "  %s" % status.pootle_path)
            self.stdout.write("   <-->  ", ending="")
            self.stdout.write("%s" % status.fs_path, self.style.FS_UPDATED)

    def handle_fs_removed(self):
        for status in self.status["fs_removed"]:
            self.stdout.write(
                "  %s" % status.pootle_path)
            self.stdout.write("   <-->  ", ending="")
            self.stdout.write("(%s)" % status.fs_path, self.style.FS_REMOVED)

    def handle_pootle_untracked(self):
        for status in self.status["pootle_untracked"]:
            self.stdout.write(
                "  %s" % status.pootle_path,
                self.style.FS_UNTRACKED)
            self.stdout.write("   <-->  ", ending="")
            self.stdout.write("(%s)" % status.fs_path, self.style.FS_MISSING)

    def handle_pootle_added(self):
        for status in self.status["pootle_added"]:
            self.stdout.write(
                "  %s" % status.pootle_path,
                self.style.FS_ADDED)
            self.stdout.write("   <-->  ", ending="")
            self.stdout.write("(%s)" % status.fs_path, self.style.FS_MISSING)

    def handle_pootle_removed(self):
        for status in self.status["pootle_removed"]:
            self.stdout.write(
                "  (%s)" % status.pootle_path,
                self.style.FS_REMOVED)
            self.stdout.write("   <-->  ", ending="")
            self.stdout.write("%s" % status.fs_path)

    def handle_pootle_ahead(self):
        for status in self.status["pootle_ahead"]:
            self.stdout.write(
                "  %s" % status.pootle_path,
                self.style.FS_UPDATED)
            self.stdout.write("   <-->  ", ending="")
            self.stdout.write("(%s)" % status.fs_path)

    def handle(self, project_code, *args, **options):
        self.fs = self.get_fs(project_code)
        self.pootle_path = options["pootle_path"]
        self.fs_path = options["fs_path"]
        if not self.status.has_changed:
            self.stdout.write("Everything up-to-date")
            return

        for k in self.status:
            self.handle_status(k)
