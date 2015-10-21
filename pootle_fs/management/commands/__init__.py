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
        try:
            self.project = Project.objects.get(code=project_code)
        except Project.DoesNotExist:
            raise CommandError(
                "Unrecognised project: %s" % project_code)
        return self.project

    def write_line(self, pootle_path, fs_path,
                   pootle_style=None, fs_style=None):
        self.stdout.write("  %s" % pootle_path, pootle_style)
        self.stdout.write("   <-->  ", ending="")
        self.stdout.write(fs_path, fs_style)


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

    def handle_added_from_pootle(self, action):
        if action.original_status.status in ["conflict", "conflict_untracked"]:
            return action.pootle_path, action.fs_path
        else:
            return (
                action.pootle_path,
                "(%s)" % action.fs_path,
                None, self.style.FS_MISSING)

    def handle_fetched_from_fs(self, action):
        if action.original_status.status in ["conflict", "conflict_untracked"]:
            return action.pootle_path, action.fs_path
        else:
            return (
                "(%s)" % action.pootle_path,
                action.fs_path,
                self.style.FS_MISSING)

    def handle_staged_for_removal(self, action):
        file_exists = (
            action.original_status.status
            in ["fs_untracked", "pootle_removed", "conflict_untracked"])
        store_exists = (
            action.original_status.status
            in ["pootle_untracked", "fs_removed", "conflict_untracked"])
        if file_exists:
            fs_path = action.fs_path
        else:
            fs_path = "(%s)" % action.fs_path
        if store_exists:
            pootle_path = action.pootle_path
        else:
            pootle_path = "(%s)" % action.pootle_path
        return pootle_path, fs_path

    def handle_removed(self, action):
        return(
            "(%s)" % action.pootle_path,
            "(%s)" % action.fs_path,
            self.style.POOTLE_MISSING,
            self.style.FS_MISSING)

    def handle_actions(self, action_type):
        failed = self.response.failed(action_type)
        title = self.response.get_action_title(action_type)
        if any(failed):
            self.stdout.write(title, self.style.ERROR)
        else:
            self.stdout.write(title, self.style.HTTP_INFO)
        self.stdout.write("-" * len(title))
        self.stdout.write(self.response.get_action_description(action_type))
        self.stdout.write("")
        for action in self.response.completed(action_type):
            handler = getattr(self, "handle_%s" % action_type, None)
            if handler:
                self.write_line(*handler(action))
            else:
                self.write_line(action.pootle_path, action.fs_path)
        if any(failed):
            for action in failed:
                self.write_line(
                    action.pootle_path,
                    action.fs_path,
                    fs_style=self.style.FS_ERROR,
                    pootle_style=self.style.POOTLE_ERROR)
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
        return self.handle(*args, **options)
