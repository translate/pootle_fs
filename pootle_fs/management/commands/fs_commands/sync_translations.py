#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_fs.management.commands import TranslationsSubCommand


class SyncTranslationsCommand(TranslationsSubCommand):
    help = "Sync translations into Pootle from FS."

    def handle(self, project_code, *args, **options):
        self.handle_response(
            self.get_fs(project_code).sync_translations(
                fs_path=options['fs_path'],
                pootle_path=options['pootle_path']))
