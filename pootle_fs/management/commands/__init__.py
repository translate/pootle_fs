#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from optparse import make_option
import os
import sys

from django.core.management.base import (
    BaseCommand, CommandError, OutputWrapper)
from django.core.management.color import no_style
from django.utils.functional import cached_property

from pootle_project.models import Project

from pootle_fs.models import ProjectFS


class SubCommand(BaseCommand):

    requires_system_checks = False

    def get_fs(self, project_code):
        self.get_project(project_code)
        try:
            self.fs = self.project.fs.get()
            return self.fs
        except ProjectFS.DoesNotExist:
            raise CommandError(
                "Project (%s) is not managed in FS"
                % self.project.code)

    def get_project(self, project_code):
        self.project = Project.objects.get(code=project_code)
        return self.project


class TranslationsSubCommand(SubCommand):
    shared_option_list = (
        make_option(
            '-p', '--fs_path', action='store', dest='fs_path',
            help='Filter translations by filesystem path'),
        make_option(
            '-P', '--pootle_path', action='store', dest='pootle_path',
            help='Filter translations by Pootle path'))
    option_list = SubCommand.option_list + shared_option_list

    @cached_property
    def plugin(self):
        if hasattr(self, "fs"):
            return self.fs.plugin

    def handle_actions(self, action_type):
        failed = self.response.failed(action_type)
        title = self.response.get_action_title(action_type)
        if failed:
            self.stdout.write(title, self.style.ERROR)
        else:
            self.stdout.write(title, self.style.HTTP_INFO)
        self.stdout.write("-" * len(title))
        self.stdout.write(self.response.get_action_description(action_type))
        self.stdout.write("")
        for action in self.response.completed(action_type):
            self.stdout.write("  %s" % action.pootle_path)
            self.stdout.write("   <-->  %s" % action.fs_path)
        for action in failed:
            self.stdout.write(
                "  %s" % action.pootle_path, self.style.FS_ERROR)
            self.stdout.write(
                "   <-->  %s" % action.fs_path, self.style.FS_ERROR)
        self.stdout.write("")

    def handle_response(self, response):
        self.response = response
        for action_type in self.response:
            self.handle_actions(action_type)
        return self.response

    def execute(self, *args, **options):
        """
        Overridden to return response object rather than writing to stdout
        """
        self.stdout = OutputWrapper(options.get('stdout', sys.stdout))
        if options.get('no_color'):
            self.style = no_style()
            self.stderr = OutputWrapper(options.get('stderr', sys.stderr))
            os.environ[str("DJANGO_COLORS")] = str("nocolor")
        else:
            self.stderr = OutputWrapper(
                options.get('stderr', sys.stderr), self.style.ERROR)

        if self.can_import_settings:
            from django.conf import settings
            settings

        saved_locale = None
        if not self.leave_locale_alone:
            if not self.can_import_settings:
                raise CommandError(
                    "Incompatible values of 'leave_locale_alone' "
                    "(%s) and 'can_import_settings' (%s) command "
                    "options."
                    % (self.leave_locale_alone, self.can_import_settings))
            from django.utils import translation
            saved_locale = translation.get_language()
            translation.activate('en-us')
        output = None
        try:
            run_checks = (
                self.requires_system_checks
                and not options.get('skip_validation')
                and not options.get('skip_checks'))
            if run_checks:
                self.check()
            output = self.handle(*args, **options)
        finally:
            if saved_locale is not None:
                translation.activate(saved_locale)
        return output
