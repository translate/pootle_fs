#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_fs.management.commands import SubCommand


class FilesCommand(SubCommand):
    help = "List FS translations files managed by Pootle."

    def handle(self, project, *args, **options):
        fs = self.get_fs(project)
        files = fs.list_translation_files()
        for store_fs in files.order_by("path").iterator():
            self.stdout.write(
                " %-50s %-50s %-12s %-12s \n"
                % (store_fs.path,
                   store_fs.store.pootle_path,
                   store_fs.last_sync_revision,
                   (store_fs.last_sync_commit or '')[:8]))
