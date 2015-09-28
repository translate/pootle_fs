import io
import logging
import os
from ConfigParser import ConfigParser

from django.conf import settings

from pootle_language.models import Language
from pootle_store.models import Store

from .files import FSFile
from .finder import TranslationFileFinder

logger = logging.getLogger(__name__)


class Plugin(object):
    name = None
    file_class = FSFile

    def __init__(self, fs):
        from .models import ProjectFS
        if not isinstance(fs, ProjectFS):
            raise TypeError(
                "pootle_fs.Plugin expects a ProjectFS")
        self.fs = fs

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
        return StoreFS.objects.filter(
            store__translation_project__project=self.project)

    def fetch_translations(self):
        for fs_file in self.find_translations():
            fs_file.fetch()

    def find_translations(self):
        config = self.read_config()

        for section in config.sections():
            if section == "default":
                section_subdirs = []
            else:
                section_subdirs = section.split("/")

            finder = TranslationFileFinder(
                os.path.join(
                    self.local_fs_path,
                    config.get(section, "translation_path")))
            for file_path, matched in finder.find():
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
                       matched.get('directory_path', '').strip("/").split("/")
                       if m])
                yield self.file_class(
                    "/".join(
                        ["", self.project.code, language.code]
                        + subdirs
                        + [matched.get("filename")
                           or os.path.basename(file_path)]),
                    file_path.replace(self.local_fs_path, ""))

    def pull_translations(self):
        for fs_file in self.find_translations():
            fs_file.pull()

    def pull(self):
        pass

    def push(self):
        pass

    def read(self, path):
        target = os.path.join(self.local_fs_path, path)
        with open(target) as f:
            content = f.read()
        return content

    def read_config(self):
        self.pull()
        config = ConfigParser()
        config.readfp(io.BytesIO(self.read(self.fs.pootle_config)))
        return config

    def status(self):
        self.pull()
        status = dict(
            CONFLICT=[],
            FS_ADDED=[],
            FS_AHEAD=[],
            POOTLE_AHEAD=[])

        for store_fs in self.translation_files:
            fs_file = store_fs.file
            fs_removed = not fs_file.exists
            fs_added = (
                store_fs.last_sync_hash is None)
            fs_changed = (
                store_fs.last_sync_hash is not None
                and (fs_file.latest_commit
                     != store_fs.last_sync_hash))
            pootle_changed = (
                store_fs.last_sync_hash is not None
                and (store_fs.store.get_max_unit_revision()
                     != store_fs.last_sync_revision))
            if fs_removed:
                status['FS_REMOVED'].append(store_fs)
            elif fs_added:
                status['FS_ADDED'].append(store_fs)
            elif fs_changed and pootle_changed:
                status['CONFLICT'].append(store_fs)
            elif fs_changed:
                status['FS_AHEAD'].append(store_fs)
            elif pootle_changed:
                status['POOTLE_AHEAD'].append(store_fs)

        status['POOTLE_ADDED'] = self.stores.filter(fs__isnull=True)

        return status


class Plugins(object):

    def __init__(self):
        self.__plugins__ = {}

    def register(self, plugin):
        self.__plugins__[plugin.name] = plugin

    def __getitem__(self, k):
        return self.__plugins__[k]

    def __contains__(self, k):
        return k in self.__plugins__
