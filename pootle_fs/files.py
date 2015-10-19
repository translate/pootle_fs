# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os

from django.utils.functional import cached_property

from translate.storage.factory import getclass

from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_statistics.models import SubmissionTypes
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject

from .models import FS_WINS, POOTLE_WINS, StoreFS


logger = logging.getLogger(__name__)


class FSFile(object):

    def __init__(self, fs_store):
        """
        :param fs_store: ``FSStore`` object
        """
        if not isinstance(fs_store, StoreFS):
            raise TypeError(
                "pootle_fs.FSFile expects a StoreFS")
        self.fs_store = fs_store
        self.pootle_path = fs_store.pootle_path
        self.path = fs_store.path

    def __str__(self):
        return "<%s: %s::%s>" % (
            self.__name__, self.pootle_path, self.path)

    @property
    def directory(self):
        if self.fs_store.store:
            return self.fs_store.store.parent
        if not self.translation_project:
            return
        directory = self.translation_project.directory
        if self.directory_path:
            for subdir in self.directory_path.split("/"):
                try:
                    directory = directory.child_dirs.get(name=subdir)
                except Directory.DoesNotExist:
                    return
        return directory

    @property
    def directory_path(self):
        return '/'.join(self.pootle_path.split("/")[3:-1])

    @property
    def exists(self):
        return os.path.exists(self.file_path)

    @property
    def filename(self):
        return self.pootle_path.split("/")[-1]

    @property
    def file_path(self):
        return os.path.join(
            self.fs.plugin.local_fs_path,
            self.path.strip("/"))

    @cached_property
    def fs(self):
        return self.project.fs.get()

    @property
    def fs_changed(self):
        latest_hash = self.latest_hash
        return (
            latest_hash
            and (
                latest_hash
                != self.fs_store.last_sync_hash))

    @cached_property
    def language(self):
        if self.fs_store.store:
            return self.fs_store.store.translation_project.language
        return Language.objects.get(code=self.pootle_path.split("/")[1])

    @property
    def latest_hash(self):
        raise NotImplementedError

    @property
    def plugin(self):
        return self.fs.plugin

    @property
    def pootle_changed(self):
        return (
            self.store
            and (
                self.store.get_max_unit_revision()
                != self.fs_store.last_sync_revision))

    @property
    def project(self):
        return self.fs_store.project

    @property
    def store(self):
        if self.fs_store.store:
            return self.fs_store.store
        try:
            return Store.objects.get(
                pootle_path=self.pootle_path)
        except Store.DoesNotExist:
            return

    @property
    def translation_project(self):
        if self.fs_store.store:
            return self.fs_store.store.translation_project
        try:
            return self.project.translationproject_set.get(
                language=self.language)
        except TranslationProject.DoesNotExist:
            return

    def add(self):
        logger.debug("Adding file: %s" % self.path)
        self.fs_store.resolve_conflict = POOTLE_WINS
        self.fs_store.save()

    def create_store(self):
        """
        Creates a ```Store``` and if necessary the ```TranslationProject```
        parent ```Directories```
        """
        if not self.translation_project:
            logger.debug(
                "Created translation project: %s/%s"
                % (self.project.code, self.language.code))
            tp = TranslationProject.objects.create(
                project=self.project,
                language=self.language)
            tp.directory.obsolete = False
            tp.directory.save()
        if not self.directory:
            directory = self.translation_project.directory
            if self.directory_path:
                for subdir in self.directory_path.split("/"):
                    directory, created = directory.child_dirs.get_or_create(
                        name=subdir)
                    if created:
                        logger.debug(
                            "Created directory: %s" % directory.path)
        if not self.store:
            store, created = Store.objects.get_or_create(
                parent=self.directory, name=self.filename,
                translation_project=self.translation_project)
            if created:
                store.save()
                logger.debug("Created Store: %s" % store.pootle_path)
        if not self.fs_store.store == self.store:
            self.fs_store.store = self.store
            self.fs_store.save()

    def delete(self):
        """
        Delete the file from FS and Pootle

        This does not commit/push
        """
        store = self.store
        if store and store.pk:
            store.makeobsolete()
        if self.fs_store.pk:
            self.fs_store.delete()
        self.remove_file()

    def fetch(self):
        """
        Called when FS file is fetched
        """
        logger.debug("Fetching file: %s" % self.path)
        if self.store and not self.fs_store.store:
            self.fs_store.store = self.store
        self.fs_store.resolve_conflict = FS_WINS
        self.fs_store.save()
        return self.fs_store

    def on_sync(self, latest_hash, revision):
        """
        Called after FS and Pootle have been synced
        """
        self.fs_store.resolve_conflict = None
        self.fs_store.staged_for_merge = False
        self.fs_store.last_sync_hash = latest_hash
        self.fs_store.last_sync_revision = revision
        self.fs_store.save()
        logger.debug("File synced: %s" % self.path)

    def pull(self):
        """
        Pull FS file into Pootle
        """
        logger.debug("Pulling file: %s" % self.path)
        if not self.store:
            self.create_store()
        if not self.fs_store.store == self.store:
            self.fs_store.store = self.store
            self.fs_store.save()
        self.sync_to_pootle()

    def push(self):
        """
        Push Pootle ``Store`` into FS
        """
        current_revision = self.store.get_max_unit_revision()
        last_revision = self.fs_store.last_sync_revision
        if self.exists:
            if last_revision and (last_revision == current_revision):
                return
        logger.debug("Pushing file: %s" % self.path)
        directory = os.path.dirname(self.fs_store.file.file_path)
        if not os.path.exists(directory):
            logger.debug("Creating directory: %s" % directory)
            os.makedirs(directory)
        self.sync_from_pootle()

    def read(self):
        with open(self.file_path) as f:
            return f.read()

    def remove_file(self):
        if self.exists:
            os.unlink(self.file_path)

    def sync_from_pootle(self):
        """
        Update FS file with the serialized content from Pootle ```Store```
        """
        with open(self.file_path, "w") as f:
            f.write(self.store.serialize())
        logger.debug("Pushed file: %s" % self.path)

    def sync_to_pootle(self, pootle_wins=False, merge=False):
        """
        Update Pootle ``Store`` with the parsed FS file.
        """
        with open(self.file_path) as f:
            if merge:
                revision = self.fs_store.last_sync_revision
            else:
                revision = self.store.get_max_unit_revision() + 1
            tmp_store = getclass(f)(f.read())
            self.store.update(
                overwrite=True,
                store=tmp_store,
                submission_type=SubmissionTypes.UPLOAD,
                user=self.plugin.pootle_user,
                revision=revision,
                pootle_wins=pootle_wins)
        logger.debug("Pulled file: %s" % self.path)
        self.on_sync(
            self.latest_hash,
            self.store.get_max_unit_revision())
