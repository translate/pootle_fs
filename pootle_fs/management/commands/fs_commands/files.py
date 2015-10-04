#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_fs.management.commands import TranslationsSubCommand


class FilesCommand(TranslationsSubCommand):
    help = "List FS translations files managed by Pootle."

    def handle(self, project_code, *args, **options):
        self.fs = self.get_fs(project_code)
        status = self.fs.status()
        for store_fs in status.get_up_to_date().order_by("path").iterator():
            self.stdout.write(
                "  %s (%s)"
                % (store_fs.pootle_path, store_fs.last_sync_revision))
            self.stdout.write(
                "   <-->  %s (%s)"
                % (store_fs.path, (store_fs.last_sync_hash or "")[:8]))
