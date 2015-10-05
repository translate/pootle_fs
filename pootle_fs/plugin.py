from fnmatch import fnmatch
import io
import logging
import os
from ConfigParser import ConfigParser

from django.conf import settings

from pootle_language.models import Language
from pootle_store.models import Store

from .files import FSFile
from .finder import TranslationFileFinder
from .models import FS_WINS, POOTLE_WINS
from .status import ProjectFSStatus


logger = logging.getLogger(__name__)


class Plugin(object):
    name = None
    file_class = FSFile
    status_class = ProjectFSStatus
    finder_class = TranslationFileFinder

    def __init__(self, fs):
        from .models import ProjectFS
        if not isinstance(fs, ProjectFS):
            raise TypeError(
                "pootle_fs.Plugin expects a ProjectFS")
        self.fs = fs

    @property
    def addable_translations(self):
        for store in self.stores.filter(fs__isnull=True):
            fs_path = self.get_fs_path(store.pootle_path)
            if fs_path:
                yield store, fs_path

    @property
    def is_cloned(self):
        if os.path.exists(self.local_fs_path):
            return True
        return False

    @property
    def local_fs_path(self):
        return os.path.join(
            settings.POOTLE_FS_PATH, self.fs.project.code)

    @property
    def project(self):
        return self.fs.project

    @property
    def stores(self):
        return Store.objects.filter(
            translation_project__project=self.project)

    @property
    def translations(self):
        from .models import StoreFS
        return StoreFS.objects.filter(project=self.project)

    @property
    def unsynced_translations(self):
        return (self.translations.filter(last_sync_revision__isnull=True)
                                 .filter(last_sync_hash__isnull=True))

    @property
    def synced_translations(self):
        return (self.translations.exclude(last_sync_revision__isnull=True)
                                 .exclude(last_sync_hash__isnull=True))

    @property
    def conflicting_translations(self):
        unresolved = self.synced_translations.filter(
            resolve_conflict__isnull=True)
        for translation in unresolved:
            fs_file = translation.file
            if fs_file.fs_changed and fs_file.pootle_changed:
                yield translation

    def get_finder(self, translation_path):
        return self.finder_class(
            os.path.join(
                self.local_fs_path,
                translation_path))

    def add_translations(self, force=False, pootle_path=None, fs_path=None):
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
        self.pull()
        for store, path in self.addable_translations:
            if pootle_path is not None:
                if not fnmatch(store.pootle_path, pootle_path):
                    continue
            if fs_path is not None:
                if not fnmatch(path, fs_path):
                    continue
            fs_store = StoreFS.objects.create(
                project=self.project,
                store=store,
                path=path)
            if fs_store.file.exists and not force:
                fs_store.delete()
            else:
                # Mark this as added from FS in case of any conflict
                fs_store.resolve_conflict = POOTLE_WINS
                fs_store.save()
        if force:
            for translation in self.conflicting_translations:
                if fs_path is not None:
                    if not fnmatch(translation.path, fs_path):
                        continue
                if pootle_path is not None:
                    if not fnmatch(translation.pootle_path, pootle_path):
                        continue
                translation.resolve_conflict = POOTLE_WINS
                translation.save()

    def fetch_translations(self, force=False, pootle_path=None, fs_path=None):
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
        self.pull()
        status = self.status(pootle_path=pootle_path, fs_path=fs_path)
        to_create = status["fs_untracked"]
        if force:
            to_create += status["conflict_untracked"]

        for fs_status in to_create:
            fs_store = StoreFS.objects.create(
                project=self.project,
                pootle_path=fs_status.pootle_path,
                path=fs_status.fs_path)
            fs_store.resolve_conflict = FS_WINS
            fs_store.save()
            fs_store.file.fetch()
        if force:
            for translation in self.conflicting_translations:
                if fs_path is not None:
                    if not fnmatch(translation.path, fs_path):
                        continue
                if pootle_path is not None:
                    if not fnmatch(translation.pootle_path, pootle_path):
                        continue
                translation.resolve_conflict = FS_WINS
                translation.save()

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
                lang_code = matched['lang']
                try:
                    language = Language.objects.get(code=lang_code)
                except Language.DoesNotExist:
                    logger.warning(
                        "Language does not exist for %s: %s"
                        % (self.fs, lang_code))
                    continue
                subdirs = (
                    section_subdirs
                    + [m for m in
                       matched.get('directory_path', '').split("/")
                       if m])
                _pootle_path = "/".join(
                    ["", language.code, self.project.code]
                    + subdirs
                    + [matched.get("filename")
                       or os.path.basename(file_path)])
                if pootle_path is not None:
                    if not fnmatch(_pootle_path, pootle_path):
                        continue
                yield _pootle_path, path

    def get_fs_path(self, pootle_path):
        """
        Reverse match an FS filepath from a ``Store`` using the project config.

        :param store: A ``Store`` object to get the FS filepath for
        :returns: An filepath relative to the FS root.
        """
        parts = pootle_path.strip("/").split("/")
        lang_code = parts[0]
        subdirs = parts[2:-1]
        filename = parts[-1]
        fs_path = None
        config = self.read_config()
        if subdirs:
            if config.has_section(subdirs[0]):
                finder = self.get_finder(
                    config.get(subdirs[0], "translation_path"))
                fs_path = finder.reverse_match(
                    lang_code, filename, '/'.join(subdirs[1:]))
                if fs_path:
                    fs_path = fs_path.replace(self.local_fs_path, "")
        if not fs_path:
            finder = self.get_finder(
                config.get("default", "translation_path"))
            fs_path = finder.reverse_match(
                lang_code, filename, '/'.join(subdirs))
            if fs_path:
                fs_path = fs_path.replace(self.local_fs_path, "")
        if fs_path:
            return "/%s" % fs_path.lstrip("/")

    def pull_translations(self, prune=False, pootle_path=None, fs_path=None):
        """
        :param prune: Remove files that do not exist in the FS.
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        """
        status = self.status(pootle_path=pootle_path, fs_path=fs_path)
        for fs_status in (status['fs_added'] + status['fs_ahead']):
            fs_status.store_fs.file.pull()

        if prune:
            prunable = status['fs_removed'] + status["pootle_untracked"]
            for fs_status in prunable:
                if fs_status.store_fs:
                    fs_status.store_fs.file.delete()
                else:
                    Store.objects.get(
                        pootle_path=fs_status.pootle_path).delete()

    def pull(self):
        """
        Pull the FS from external source if required.
        """
        pass

    def push(self, message=None):
        """
        Push the FS to an external source if required.
        """
        pass

    def push_translations(self, prune=False, pootle_path=None, fs_path=None):
        """
        :param prune: Remove files that do not exist in Pootle.
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        """
        status = self.status(pootle_path=pootle_path, fs_path=fs_path)
        for fs_status in (status['pootle_added'] + status['pootle_ahead']):
            fs_status.store_fs.file.push()
        if prune:
            for fs_status in status['pootle_removed']:
                fs_status.store_fs.file.delete()
            for fs_status in status['fs_untracked']:
                os.unlink(
                    os.path.join(
                        self.local_fs_path, fs_status.fs_path.strip("/")))
        self.push()

    def read(self, path):
        target = os.path.join(self.local_fs_path, path)
        with open(target) as f:
            content = f.read()
        return content

    def read_config(self):
        """
        Read and parse the configuration for this project

        :return config: Where ``config`` is an ``ConfigParser`` instance
        """
        config = ConfigParser()
        config.readfp(io.BytesIO(self.read(self.fs.pootle_config)))
        return config

    def status(self, fs_path=None, pootle_path=None):
        """
        Get a status object for showing current status of FS/Pootle

        :return status: Where ``status`` is an instance of self.status_class
        """
        self.pull()
        return self.status_class(
            self, fs_path=fs_path, pootle_path=pootle_path)

    def _match_config_path(self, section, lang_code, subdirs, filename):
        config = self.read_config()
        if config.has_section(section):
            path = config.get(section, "translation_path")
            matching = not (
                subdirs and "<directory_path>" not in path)
            if matching:
                path = (path.replace("<lang>",
                                     lang_code)
                            .replace("<filename>",
                                     os.path.splitext(filename)[0]))
                if subdirs:
                    path = path.replace(
                        "<directory_path>", '/'.join(subdirs))
                return path


class Plugins(object):

    def __init__(self):
        self.__plugins__ = {}

    def register(self, plugin):
        self.__plugins__[plugin.name] = plugin

    def __getitem__(self, k):
        return self.__plugins__[k]

    def __contains__(self, k):
        return k in self.__plugins__
