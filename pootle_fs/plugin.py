# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from ConfigParser import ConfigParser
from fnmatch import fnmatch
import functools
import io
import logging
import os
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle_store.models import Store

from .files import FSFile
from .finder import TranslationFileFinder
from .language import LanguageMapper
from .models import FS_WINS, POOTLE_WINS, ProjectFS
from .response import ActionResponse
from .status import ProjectFSStatus


logger = logging.getLogger(__name__)


def responds_to_status(f):

    @functools.wraps(f)
    def method_wrapper(self, *args, **kwargs):
        if "response" in kwargs:
            response = kwargs["response"]
            del kwargs["response"]
        else:
            response = self.response_class(self)

        if "status" in kwargs:
            status = kwargs["status"]
            del kwargs["status"]
        else:
            status = self.status(
                pootle_path=kwargs.get("pootle_path"),
                fs_path=kwargs.get("fs_path"))
        return f(self, status, response, *args, **kwargs)
    return method_wrapper


class Plugin(object):
    name = None
    file_class = FSFile
    finder_class = TranslationFileFinder
    language_mapper_class = LanguageMapper
    status_class = ProjectFSStatus
    response_class = ActionResponse

    def __init__(self, fs):
        from .models import ProjectFS
        if not isinstance(fs, ProjectFS):
            raise TypeError(
                "pootle_fs.Plugin expects a ProjectFS")
        self.fs = fs

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.name == other.name:
                return True
        return False

    @property
    def addable_translations(self):
        addable = self.stores.exclude(obsolete=True).filter(fs__isnull=True)
        for store in addable:
            fs_path = self.get_fs_path(store.pootle_path)
            if fs_path:
                yield store, fs_path

    @property
    def is_cloned(self):
        if os.path.exists(self.local_fs_path):
            return True
        return False

    @cached_property
    def lang_mapper(self):
        config = self.read_config()
        if config.has_option("default", "lang_mapping"):
            mapping = [
                x.strip()
                for x
                in config.get("default", "lang_mapping").split("\n")
                if x.strip()]
        else:
            mapping = []
        return self.language_mapper_class(mapping)

    @property
    def local_fs_path(self):
        return os.path.join(
            settings.POOTLE_FS_PATH, self.fs.project.code)

    @property
    def pootle_user(self):
        User = get_user_model()
        config = self.read_config()
        if config.has_option("default", "pootle_user"):
            username = config.get("default", "pootle_user")
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                logger.warning(
                    "Misconfigured user in .pootle.ini: %s"
                    % username)
        return User.objects.get(username="system")

    @property
    def project(self):
        return self.fs.project

    @property
    def stores(self):
        return Store.objects.filter(
            translation_project__project=self.project)

    @property
    def synced_translations(self):
        return (self.translations.exclude(last_sync_revision__isnull=True)
                                 .exclude(last_sync_hash__isnull=True))

    @property
    def translations(self):
        from .models import StoreFS
        return StoreFS.objects.filter(project=self.project)

    @property
    def unsynced_translations(self):
        return (self.translations.filter(last_sync_revision__isnull=True)
                                 .filter(last_sync_hash__isnull=True))

    @responds_to_status
    def add_translations(self, status, response,
                         pootle_path=None, fs_path=None, force=False):
        """
        Add translations from Pootle into the FS

        If ``force``=``True`` is present it will also:
        - add untracked conflicting files from Pootle
        - mark tracked conflicting files to update from Pootle

        :param force: Add conflicting translations.
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        """
        from .models import StoreFS
        to_create = status["pootle_untracked"]
        if force:
            to_create += status["conflict_untracked"]
        for fs_status in to_create:
            StoreFS.objects.create(
                project=self.project,
                pootle_path=fs_status.pootle_path,
                path=fs_status.fs_path).file.add()
            response.add("added_from_pootle", fs_status)
        if force:
            for fs_status in status["fs_removed"]:
                fs_status.store_fs.file.add()
                response.add("added_from_pootle", fs_status)
            for fs_status in status["conflict"]:
                fs_status.store_fs.file.add()
                response.add("added_from_pootle", fs_status)
        return response

    def clear_repo(self):
        if self.is_cloned:
            shutil.rmtree(self.local_fs_path)

    @responds_to_status
    def fetch_translations(self, status, response,
                           pootle_path=None, fs_path=None, force=False):
        """
        Add translations from FS into Pootle

        If ``force``=``True`` is present it will also:
        - add untracked conflicting files from FS
        - mark tracked conflicting files to update from FS

        :param force: Add conflicting translations.
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        """
        from .models import StoreFS
        to_create = status["fs_untracked"]
        if force:
            to_create = to_create + status["conflict_untracked"]

        for fs_status in to_create:
            fs_store = StoreFS.objects.create(
                project=self.project,
                pootle_path=fs_status.pootle_path,
                path=fs_status.fs_path)
            fs_store.file.fetch()
            response.add("fetched_from_fs", fs_status)
        if force:
            for fs_status in status["pootle_removed"]:
                fs_status.store_fs.file.fetch()
                response.add("fetched_from_fs", fs_status)
            for fs_status in status["conflict"]:
                fs_status.store_fs.file.fetch()
                response.add("fetched_from_fs", fs_status)
        return response

    def find_translations(self, fs_path=None, pootle_path=None):
        """
        Find translation file from the file system

        :param force: Add conflicting translations.
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        :yields pootle_path, fs_path:
        """
        config = self.read_config()
        missing_langs = set()

        for section in config.sections():
            if section == "default":
                section_subdirs = []
            else:
                section_subdirs = section.split("/")

            finder = self.get_finder(
                config.get(section, "translation_path"))
            for file_path, matched in finder.find():
                path = file_path.replace(self.local_fs_path, "")
                if fs_path is not None:
                    if not fnmatch(path, fs_path):
                        continue
                language = self.lang_mapper[matched['lang']]
                if not language:
                    missing_langs.add(matched['lang'])
                    continue
                subdirs = (
                    section_subdirs
                    + [m for m in
                       matched.get('directory_path', '').split("/")
                       if m])
                _pootle_path = "/".join(
                    ["", language.code, self.project.code]
                    + subdirs
                    + ["%s.%s" % (matched["filename"],
                                  matched["ext"])])
                if pootle_path is not None:
                    if not fnmatch(_pootle_path, pootle_path):
                        continue
                yield _pootle_path, path
        if missing_langs:
            logger.warning(
                "Could not import files for languages: %s"
                % (", ".join(missing_langs)))

    @lru_cache(maxsize=None)
    def get_finder(self, translation_path):
        return self.finder_class(
            os.path.join(
                self.local_fs_path,
                translation_path),
            ext="po",
            template_ext=["pot"])

    @lru_cache(maxsize=None)
    def get_fs_path(self, pootle_path):
        """
        Reverse match an FS filepath from a ``Store`` using the project config.

        :param store: A ``Store`` object to get the FS filepath for
        :returns: An filepath relative to the FS root.
        """
        parts = pootle_path.strip("/").split("/")
        lang_code = self.lang_mapper.get_fs_code(parts[0])
        subdirs = parts[2:-1]
        filename = parts[-1]
        fs_path = None
        config = self.read_config()
        if subdirs:
            if config.has_section(subdirs[0]):
                finder = self.get_finder(
                    config.get(subdirs[0], "translation_path"))
                fs_path = finder.reverse_match(
                    lang_code,
                    *os.path.splitext(filename),
                    directory_path='/'.join(subdirs[1:]))
                if fs_path:
                    fs_path = fs_path.replace(self.local_fs_path, "")
        if not fs_path:
            finder = self.get_finder(
                config.get("default", "translation_path"))
            fs_path = finder.reverse_match(
                lang_code,
                *os.path.splitext(filename),
                directory_path='/'.join(subdirs))
            if fs_path:
                fs_path = fs_path.replace(self.local_fs_path, "")
        if fs_path:
            return "/%s" % fs_path.lstrip("/")

    @responds_to_status
    def merge_translations(self, status, response,
                           pootle_path=None, fs_path=None, pootle_wins=False):
        """
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        """
        from .models import StoreFS

        for fs_status in status["conflict_untracked"]:
            fs_store = StoreFS.objects.create(
                project=self.project,
                store=Store.objects.get(
                    pootle_path=fs_status.pootle_path),
                path=fs_status.fs_path)
            fs_store.staged_for_merge = True
            if pootle_wins:
                fs_store.resolve_conflict = POOTLE_WINS
                action_type = "staged_for_merge_pootle"
            else:
                fs_store.resolve_conflict = FS_WINS
                action_type = "staged_for_merge_fs"
            fs_store.save()
            response.add(action_type, fs_status)

        for fs_status in status["conflict"]:
            fs_store = fs_status.store_fs
            fs_store.staged_for_merge = True
            if pootle_wins:
                fs_store.resolve_conflict = POOTLE_WINS
                action_type = "staged_for_merge_pootle"
            else:
                fs_store.resolve_conflict = FS_WINS
                action_type = "staged_for_merge_fs"
            fs_store.save()
            response.add(action_type, fs_status)
        return response

    @responds_to_status
    def merge_translation_files(self, status, response,
                                pootle_path=None, fs_path=None):
        for fs_status in status["merge_pootle"]:
            fs_status.store_fs.file.sync_to_pootle(
                merge=True, pootle_wins=True)
            fs_status.store_fs.file.sync_from_pootle()
            fs_status.store_fs.file.on_sync(
                fs_status.store_fs.file.latest_hash,
                fs_status.store_fs.store.get_max_unit_revision())
            response.add("merged_from_pootle", fs_status)
        for fs_status in status["merge_fs"]:
            fs_status.store_fs.file.sync_to_pootle(
                merge=True, pootle_wins=False)
            fs_status.store_fs.file.sync_from_pootle()
            fs_status.store_fs.file.on_sync(
                fs_status.store_fs.file.latest_hash,
                fs_status.store_fs.store.get_max_unit_revision())
            response.add("merged_from_fs", fs_status)
        return response

    def pull(self):
        """
        Pull the FS from external source if required.
        """
        pass

    @responds_to_status
    def pull_translations(self, status, response,
                          pootle_path=None, fs_path=None):
        """
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        """
        for fs_status in (status['fs_added'] + status['fs_ahead']):
            fs_status.store_fs.file.pull()
            response.add("pulled_to_pootle", fs_status)
        return response

    def push(self, paths=None, message=None, response=None):
        """
        Push the FS to an external source if required.
        """
        return response

    @responds_to_status
    def push_translations(self, status, response,
                          pootle_path=None, fs_path=None):
        self.push_translation_files(
            status=status, pootle_path=pootle_path,
            fs_path=fs_path, response=response)
        for action_status in response.completed("pushed_to_fs"):
            fs_file = action_status.store_fs.file
            fs_file.on_sync(
                fs_file.latest_hash,
                action_status.store_fs.store.get_max_unit_revision())
        return self.push(response)

    @responds_to_status
    def push_translation_files(self, status, response,
                               pootle_path=None, fs_path=None):
        """
        :param prune: Remove files that do not exist in Pootle.
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        """
        pushable = status['pootle_added'] + status['pootle_ahead']
        for fs_status in pushable:
            fs_status.store_fs.file.push()
            response.add('pushed_to_fs', fs_status)
        return response

    def read(self, path):
        target = os.path.join(self.local_fs_path, path)
        with open(target) as f:
            content = f.read()
        return content

    def update_config(self):
        self.pull()
        config = self.read(self.fs.pootle_config)
        self.fs.current_config.save(
            self.fs.pootle_config,
            File(io.BytesIO(config)))
        self.read_config.cache_clear()
        if "lang_mapper" in self.__dict__:
            del self.__dict__["lang_mapper"]
        return config

    @lru_cache(maxsize=None)
    def read_config(self):
        """
        Read and parse the configuration for this project

        :return config: Where ``config`` is an ``ConfigParser`` instance
        """
        config = ConfigParser()
        if not self.fs.current_config:
            _conf = self.update_config()
        else:
            _conf = self.fs.current_config.file.read()
        config.readfp(io.BytesIO(_conf))
        return config

    def status(self, fs_path=None, pootle_path=None):
        """
        Get a status object for showing current status of FS/Pootle

        :return status: Where ``status`` is an instance of self.status_class
        """
        self.pull()
        return self.status_class(
            self, fs_path=fs_path, pootle_path=pootle_path)

    def reload(self):
        self.fs = ProjectFS.objects.get(pk=self.fs.pk)

    def remove_file(self, path):
        os.unlink(
            os.path.join(
                self.local_fs_path, path.strip("/")))

    @responds_to_status
    def rm_translations(self, status, response,
                        pootle_path=None, fs_path=None):
        """
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        """
        from .models import StoreFS
        untracked = (
            status["fs_untracked"] + status["pootle_untracked"])

        for fs_status in untracked:
            fs_store = StoreFS.objects.create(
                project=self.project,
                pootle_path=fs_status.pootle_path,
                path=fs_status.fs_path)
            fs_store.staged_for_removal = True
            fs_store.save()
            response.add("staged_for_removal", fs_status)

        removed = status["pootle_removed"] + status["fs_removed"]
        for fs_status in removed:
            fs_store = fs_status.store_fs
            fs_store.staged_for_removal = True
            fs_store.save()
            response.add("staged_for_removal", fs_status)
        return response

    @responds_to_status
    def remove_translation_files(self, status, response,
                                 pootle_path=None, fs_path=None):
        """
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        """
        for fs_status in status['to_remove']:
            fs_status.store_fs.file.delete()
            response.add("removed", fs_status)
        return response

    @responds_to_status
    def sync_translations(self, status, response,
                          pootle_path=None, fs_path=None):
        self.remove_translation_files(
            pootle_path=None, fs_path=None, response=response, status=status)
        self.merge_translation_files(
            pootle_path=None, fs_path=None, response=response, status=status)
        self.pull_translations(
            pootle_path=None, fs_path=None, response=response, status=status)
        self.push_translations(
            pootle_path=None, fs_path=None, response=response, status=status)
        return response


class Plugins(object):

    def __init__(self):
        self.__plugins__ = {}

    def __getitem__(self, k):
        return self.__plugins__[k]

    def __contains__(self, k):
        return k in self.__plugins__

    def register(self, plugin):
        self.__plugins__[plugin.name] = plugin
