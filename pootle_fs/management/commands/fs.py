#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os
import sys


from django.utils.termcolors import PALETTES, NOCOLOR_PALETTE

PALETTES[NOCOLOR_PALETTE]["FS_MISSING"] = {}
PALETTES["light"]["FS_MISSING"] = {'fg': 'magenta'}
PALETTES[NOCOLOR_PALETTE]["FS_UNTRACKED"] = {}
PALETTES["light"]["FS_UNTRACKED"] = {'fg': 'red'}
PALETTES[NOCOLOR_PALETTE]["FS_ADDED"] = {}
PALETTES["light"]["FS_ADDED"] = {'fg': 'green'}
PALETTES[NOCOLOR_PALETTE]["FS_UPDATED"] = {}
PALETTES["light"]["FS_UPDATED"] = {'fg': 'green'}
PALETTES[NOCOLOR_PALETTE]["FS_CONFLICT"] = {}
PALETTES["light"]["FS_CONFLICT"] = {'fg': 'red', 'opts': ('bold',)}
PALETTES[NOCOLOR_PALETTE]["FS_REMOVED"] = {}
PALETTES["light"]["FS_REMOVED"] = {'fg': 'red'}
PALETTES[NOCOLOR_PALETTE]["FS_ERROR"] = {}
PALETTES["light"]["FS_ERROR"] = {'fg': 'red', 'opts': ('bold',)}


# This must be run before importing Django.
os.environ["DJANGO_COLORS"] = "light"
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'


from django.core.management import (
    NO_DEFAULT,
    BaseCommand, CommandError, handle_default_options)
from django.core.management.base import OutputWrapper

from pootle_project.models import Project

from pootle_fs.models import ProjectFS

from .fs_commands.add_translations import AddTranslationsCommand
from .fs_commands.config import ConfigCommand
from .fs_commands.info import ProjectInfoCommand
from .fs_commands.fetch_translations import FetchTranslationsCommand
from .fs_commands.files import FilesCommand
from .fs_commands.rm_translations import RmTranslationsCommand
from .fs_commands.set_fs import SetFSCommand
from .fs_commands.status import StatusCommand
from .fs_commands.sync_translations import SyncTranslationsCommand


logger = logging.getLogger('pootle.fs')


class Command(BaseCommand):
    help = "Pootle FS."
    subcommands = {
        "add_translations": AddTranslationsCommand,
        "config": ConfigCommand,
        "info": ProjectInfoCommand,
        "fetch_translations": FetchTranslationsCommand,
        "files": FilesCommand,
        "rm_translations": RmTranslationsCommand,
        "set_fs": SetFSCommand,
        "status": StatusCommand,
        "sync_translations": SyncTranslationsCommand}

    def execute(self, *args, **kwargs):
        if args:
            project_code = args[0]
            args = args[1:]
            if project_code and not args:
                args = ["info"]
            try:
                Project.objects.get(code=project_code)
            except Project.DoesNotExist:
                raise CommandError("Unrecognised project: %s" % project_code)
            if args:
                subcommand = args[0]
                try:
                    subcommand = self.subcommands[subcommand]()
                except KeyError:
                    raise CommandError(
                        "Unrecognised command: %s" % subcommand)
                defaults = {}
                for opt in subcommand.option_list:
                    if opt.default is NO_DEFAULT:
                        defaults[opt.dest] = None
                    else:
                        defaults[opt.dest] = opt.default
                defaults.update(kwargs)
                return subcommand.execute(
                    project_code, *(args or ['info']), **defaults)
        return super(Command, self).execute(*args, **kwargs)

    def handle(self, *args, **kwargs):
        for project in Project.objects.all():
            try:
                self.stdout.write(
                    "%s\t%s"
                    % (project.code, project.fs.get().url))
            except ProjectFS.DoesNotExist:
                pass

    def run_from_argv(self, argv):
        """
        Set up any environment changes requested (e.g., Python path
        and Django settings), then run this command. If the
        command raises a ``CommandError``, intercept it and print it sensibly
        to stderr. If the ``--traceback`` option is present or the raised
        ``Exception`` is not ``CommandError``, raise it.
        """
        options = None
        try:
            if argv[2:] and not argv[2].startswith("-"):
                project_code = argv[2]
                try:
                    Project.objects.get(code=project_code)
                except Project.DoesNotExist:
                    raise CommandError(
                        "Unrecognised project: %s" % project_code)
                if argv[3:]:
                    subcommand = argv[3]
                else:
                    subcommand = "info"
                try:
                    subcommand = self.subcommands[subcommand]()
                except KeyError:
                    raise CommandError(
                        "Unrecognised command: %s" % subcommand)
                return subcommand.run_from_argv(
                    argv[:1] + [subcommand, project_code] + argv[4:])

            parser = self.create_parser(argv[0], argv[1])
            options, args = parser.parse_args(argv[2:])
            handle_default_options(options)
            self.execute(*args, **options.__dict__)
        except Exception as e:
            do_raise = (
                options
                and options.traceback
                or not isinstance(e, CommandError))
            if do_raise:
                raise

            # self.stderr is not guaranteed to be set here
            stderr = getattr(
                self, 'stderr', OutputWrapper(sys.stderr, self.style.ERROR))
            stderr.write('%s: %s' % (e.__class__.__name__, e))
            sys.exit(1)
