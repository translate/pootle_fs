#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.management.base import CommandError

from pootle_fs import plugins
from pootle_fs.management.commands import SubCommand
from pootle_fs.models import ProjectFS


class SetFSCommand(SubCommand):
    help = "Status of fs repositories."

    def handle(self, project, *args, **options):
        if not args or not len(args) == 2:
            raise CommandError("You must a FS type and FS url")

        try:
            plugins[args[0]]
        except KeyError:
            raise CommandError("Unrecognised FS type: %s" % args[0])

        try:
            fs = project.fs.get()
        except ProjectFS.DoesNotExist:
            fs = project.fs.create()

        fs.fs_type = args[0]
        fs.url = args[1]
        fs.save()
