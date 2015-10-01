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
    def addable_translations(self):
        for store in self.stores.filter(fs__isnull=True):
            fs_path = self.get_fs_path(store)
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

    def get_fs_path(self, store):
        config = self.read_config()
        parts = store.pootle_path.strip("/").split("/")
        lang_code = parts[0]
        subdirs = parts[2:-1]
        filename = parts[-1]
        if subdirs:
            section = subdirs[0]
            if config.has_section(section):
                translation_path = config.get(section, "translation_path")
                if subdirs[1:] and "<directory_path>" not in translation_path:
                    return
                return translation_path.replace(
                    "<lang>", lang_code).replace("<filename>", filename)

    def add_translations(self, path=None):
        from .models import StoreFS
        for store, path in self.addable_translations:
            StoreFS.objects.create(
                project=self.project,
                pootle_path=store.pootle_path,
                path=path)

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

    def pull_translations(self, path=None):
        for fs_file in self.translations:
            fs_file.file.pull()

    def push_translations(self, path=None):
        for fs_file in self.translations:
            fs_file.file.push()

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

    @property
    def store_fs_paths(self):
        return self.fs.translations.values_list("pootle_path", flat=True)

    @property
    def store_paths(self):
        return self.fs.stores.values_list("pootle_path", flat=True)

    def get_conflict_new(self):
        for pootle_path, path in self.fs.find_translations():
            if pootle_path in self.store_fs_paths:
                continue
            if pootle_path in self.store_paths:
                yield pootle_path, path

    def get_fs_new(self):
        for pootle_path, path in self.fs.find_translations():
            if pootle_path in self.store_fs_paths:
                continue
            yield pootle_path, path

    def get_pootle_new(self):
        for store, path in self.fs.addable_translations:
            target = os.path.join(self.fs.local_fs_path, path)
            if not os.path.exists(target):
                yield store, path

    def get_pootle_added(self):
        for store_fs in self.fs.unsynced_translations:
            if not store_fs.file.exists and not store_fs.store:
                # orphaned - delete?
                pass
            elif store_fs.store:
                yield store_fs

    def get_fs_added(self):
        for store_fs in self.fs.unsynced_translations:
            if not store_fs.file.exists and not store_fs.store:
                # orphaned - delete?
                pass
            elif store_fs.file.exists:
                yield store_fs

    def get_fs_removed(self):
        for store_fs in self.fs.synced_translations:
            if not store_fs.file.exists and store_fs.store:
                yield store_fs

    def get_pootle_removed(self):
        for store_fs in self.fs.synced_translations:
            if store_fs.file.exists and not store_fs.store:
                yield store_fs

    def get_both_removed(self):
        for store_fs in self.fs.synced_translations:
            if not store_fs.file.exists and not store_fs.store:
                yield store_fs

    def _get_changes(self, store_fs):
        fs_file = store_fs.file
        fs_changed = (
            fs_file.latest_hash
            != store_fs.last_sync_hash)
        pootle_changed = (
            store_fs.store.get_max_unit_revision()
            != store_fs.last_sync_revision)
        return pootle_changed, fs_changed

    def get_fs_ahead(self):
        for store_fs in self.fs.synced_translations:
            pootle_changed, fs_changed = self._get_changes(store_fs)
            if fs_changed and not pootle_changed:
                yield store_fs

    def get_pootle_ahead(self):
        for store_fs in self.fs.synced_translations:
            pootle_changed, fs_changed = self._get_changes(store_fs)
            if not fs_changed and pootle_changed:
                yield store_fs

    def get_conflict(self):
        for store_fs in self.fs.synced_translations:
            pootle_changed, fs_changed = self._get_changes(store_fs)
            if fs_changed and pootle_changed:
                yield store_fs

    def __init__(self, fs):
        self.fs = fs
        self.__status__ = dict(
            conflict=set(),
            conflict_new=set(),
            fs_added=set(),
            fs_ahead=set(),
            fs_new=set(),
            fs_removed=set(),
            pootle_ahead=set(),
            pootle_new=set(),
            pootle_added=set(),
            pootle_removed=set())

        for conflict_new in self.get_conflict_new():
            self.add("conflict_new", conflict_new)

        for conflict in self.get_conflict():
            self.add("conflict", conflict)

        for pootle_new in self.get_pootle_new():
            self.add("pootle_new", pootle_new)

        for pootle_added in self.get_pootle_added():
            self.add("pootle_added", pootle_added)

        for pootle_removed in self.get_pootle_removed():
            self.add("pootle_removed", pootle_removed)

        for pootle_ahead in self.get_pootle_ahead():
            self.add("pootle_ahead", pootle_ahead)

        for fs_new in self.get_fs_new():
            self.add("fs_new", fs_new)

        for fs_added in self.get_fs_added():
            self.add("fs_added", fs_added)

        for fs_removed in self.get_fs_removed():
            self.add("fs_removed", fs_removed)

        for fs_ahead in self.get_fs_ahead():
            self.add("fs_ahead", fs_ahead)

    def __getitem__(self, k):
        return self.__status__[k]

    def __contains__(self, k):
        return k in self.__status__ and self.__status__[k]

    def __str__(self):
        if self.has_changed:
            return (
                "<ProjectFSStatus(%s): %s>"
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
