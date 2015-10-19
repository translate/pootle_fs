#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import io
from optparse import make_option

from pootle_fs.management.commands import SubCommand


class ConfigCommand(SubCommand):
    help = "Print config."

    shared_option_list = (
        make_option('-u', '--update', action='store_true', dest='update',
                    help='Status type'), )
    option_list = SubCommand.option_list + shared_option_list

    def handle(self, project_code, *args, **options):
        if options["update"]:
            self.get_fs(project_code).plugin.update_config()
            self.stdout.write("Config updated")
            return
        config = io.BytesIO()
        self.get_fs(project_code).plugin.read_config().write(config)
        config.seek(0)
        conf = config.read()
        config.seek(0)
        self.stdout.write(conf)
