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
    def store_fs(self):
        from .models import StoreFS
        return StoreFS.objects.filter(project=self.project)

    def fetch_translations(self):
        from .models import StoreFS
        for pootle_path, path in self.find_translations():
            fs_store, created = StoreFS.objects.get_or_create(
                project=self.project,
                pootle_path=pootle_path,
                path=path)
            fs_store.file.fetch()

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
                       matched.get('directory_path', '').split("/")
                       if m])

                pootle_path = "/".join(
                    ["", language.code, self.project.code]
                    + subdirs
                    + [matched.get("filename")
                       or os.path.basename(file_path)])
                path = file_path.replace(self.local_fs_path, "")
                yield pootle_path, path

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
        return ProjectFSStatus(self)


class Plugins(object):

    def __init__(self):
        self.__plugins__ = {}

    def register(self, plugin):
        self.__plugins__[plugin.name] = plugin

    def __getitem__(self, k):
        return self.__plugins__[k]

    def __contains__(self, k):
        return k in self.__plugins__


class ProjectFSStatus(object):

    def __init__(self, fs):
        self.fs = fs
        self.__status__ = dict(
            conflict=set(),
            fs_added=set(),
            fs_ahead=set(),
            pootle_ahead=set(),
            pootle_added=set())
        for store_fs in self.fs.store_fs:
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
                self.add("fs_removed", store_fs)
            elif fs_added:
                self.add("fs_added", store_fs)
            elif fs_changed and pootle_changed:
                self.add("conflict", store_fs)
            elif fs_changed:
                self.add("fs_ahead", store_fs)
            elif pootle_changed:
                self.add("pootle_ahead", store_fs)
        for store in self.fs.stores.filter(fs__isnull=True):
            self.add("pootle_added", store)

    def __getitem__(self, k):
        return self.__status__[k]

    def __contains__(self, k):
        return k in self.__status__ and self.__status__[k]

    def __str__(self):
        if self.has_changed:
            return ("<ProjectFSStatus(%s): %s>"
                    % (self.fs.project,
                       ', '.join(["%s: %s" % (k, len(v))
                                  for k, v in self.__status__.items()
                                  if v])))
        return "<ProjectFSStatus(%s): Everything up-to-date>" % self.fs.project

    @property
    def has_changed(self):
        return any(self.__status__.values())

    def add(self, k, v):
        if k in self.__status__:
            self.__status__[k].add(v)
