#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.management.base import BaseCommand, CommandError

from pootle_fs.models import ProjectFS


class SubCommand(BaseCommand):

    requires_system_checks = False

    def get_fs(self, project):
        try:
            return project.fs.get()
        except ProjectFS.DoesNotExist:
            raise CommandError(
                "Project (%s) is not managed in FS"
                % project.code)
