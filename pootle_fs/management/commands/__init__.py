#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from pootle_project.models import Project

from pootle_fs.models import ProjectFS


class SubCommand(BaseCommand):

    requires_system_checks = False

    def get_project(self, project_code):
        self.project = Project.objects.get(code=project_code)
        return self.project

    def get_fs(self, project_code):
        self.get_project(project_code)
        try:
            return self.project.fs.get()
        except ProjectFS.DoesNotExist:
            raise CommandError(
                "Project (%s) is not managed in FS"
                % self.project.code)


class TranslationsSubCommand(SubCommand):
    shared_option_list = (
        make_option(
            '-p', '--fs_path', action='store', dest='fs_path',
            help='Filter translations by filesystem path'),
        make_option(
            '-P', '--pootle_path', action='store', dest='pootle_path',
            help='Filter translations by Pootle path'))
    option_list = SubCommand.option_list + shared_option_list
    __plugin__ = None

    @property
    def plugin(self):
        if not self.__plugin__ and hasattr(self, "fs"):
            self.__plugin__ = self.fs.plugin
        return self.__plugin__
