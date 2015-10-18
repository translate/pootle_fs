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


class MergeTranslationsCommand(TranslationsSubCommand):
    help = "Merge translations between Pootle and FS."

    shared_option_list = (
        make_option('--pootle-wins',
                    action='store_true', dest='pootle_wins',
                    help='Status type'), )
    option_list = TranslationsSubCommand.option_list + shared_option_list

    def handle(self, project_code, *args, **options):
        self.handle_response(
            self.get_fs(project_code).merge_translations(
                fs_path=options['fs_path'],
                pootle_path=options['pootle_path'],
                pootle_win=options["pootle_wins"]))
