# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from optparse import make_option

from pootle_fs.management.commands import TranslationsSubCommand


class StatusCommand(TranslationsSubCommand):
    help = "Status of fs repositories."
    __status__ = None

    shared_option_list = (
        make_option(
            '-t', '--type', action='append', dest='status_type',
            help='Status type'), )
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
        handler = getattr(self, "handle_%s" % status_type)
        for status in self.status[status_type]:
            self.write_line(*handler(status))
        self.stdout.write("")

    def handle_conflict(self, status):
        return (
            status.pootle_path,
            status.fs_path,
            self.style.FS_CONFLICT,
            self.style.FS_CONFLICT)

    def handle_conflict_untracked(self, status):
        return (
            status.pootle_path,
            status.fs_path,
            self.style.FS_CONFLICT,
            self.style.FS_CONFLICT)

    def handle_fs_untracked(self, status):
        return (
            "(%s)" % status.pootle_path,
            status.fs_path,
            self.style.FS_MISSING,
            self.style.FS_UNTRACKED)

    def handle_fs_added(self, status):
        return (
            "(%s)" % status.pootle_path,
            status.fs_path,
            self.style.FS_MISSING,
            self.style.FS_ADDED)

    def handle_fs_ahead(self, status):
        return (
            status.pootle_path,
            status.fs_path,
            None,
            self.style.FS_UPDATED)

    def handle_fs_removed(self, status):
        return (
            status.pootle_path,
            "(%s)" % status.fs_path,
            None,
            self.style.FS_REMOVED)

    def handle_pootle_untracked(self, status):
        return (
            status.pootle_path,
            "(%s)" % status.fs_path,
            self.style.FS_UNTRACKED,
            self.style.FS_REMOVED)

    def handle_pootle_added(self, status):
        return (
            status.pootle_path,
            "(%s)" % status.fs_path,
            self.style.FS_ADDED,
            self.style.FS_REMOVED)

    def handle_pootle_removed(self, status):
        return (
            "(%s)" % status.pootle_path,
            status.fs_path,
            self.style.FS_REMOVED)

    def handle_pootle_ahead(self, status):
        return (
            status.pootle_path,
            status.fs_path,
            self.style.FS_UPDATED)

    def handle_merge_fs(self, status):
        return (
            status.pootle_path,
            status.fs_path,
            self.style.FS_UPDATED,
            self.style.FS_UPDATED)

    def handle_merge_pootle(self, status):
        return (
            status.pootle_path,
            status.fs_path,
            self.style.FS_UPDATED,
            self.style.FS_UPDATED)

    def handle_to_remove(self, status):
        if status.store_fs.file.exists:
            pootle_path = "(%s)" % status.pootle_path
            fs_path = status.fs_path
        else:
            pootle_path = status.pootle_path
            fs_path = "(%s)" % status.fs_path
        return (
            pootle_path,
            fs_path,
            self.style.FS_MISSING,
            self.style.FS_MISSING)

    def handle(self, project_code, *args, **options):
        self.fs = self.get_fs(project_code)
        self.pootle_path = options["pootle_path"]
        self.fs_path = options["fs_path"]
        if not self.status.has_changed:
            self.stdout.write("Everything up-to-date")
            return

        for k in self.status:
            self.handle_status(k)
