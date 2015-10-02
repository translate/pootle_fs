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

    @property
    def conflicting_translations(self):
        unresolved = self.synced_translations.filter(
            resolve_conflict__isnull=True)
        for translation in unresolved:
            fs_file = translation.file
            if fs_file.fs_changed and fs_file.pootle_changed:
                yield translation

    def add_translations(self, pootle_path=None, fs_path=None, force=False):
        from .models import StoreFS
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

    def fetch_translations(self, pootle_path=None, fs_path=None, force=False):
        from .models import StoreFS
        found_translations = self.find_translations(
            fs_path=fs_path, pootle_path=pootle_path)
        for _pootle_path, path in found_translations:
            fs_store, created = StoreFS.objects.get_or_create(
                project=self.project,
                pootle_path=_pootle_path,
                path=path)
            if not force and (created and fs_store.store):
                # conflict
                fs_store.delete()
            elif created:
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

    def _match_config_path(self, section, lang_code, subdirs, filename):
        config = self.read_config()
        if config.has_section(section):
            translation_path = config.get(section, "translation_path")
            matching = not (
                subdirs
                and "<directory_path>" not in translation_path)
            if matching:
                return translation_path.replace(
                    "<lang>", lang_code).replace("<filename>", filename)

    def get_fs_path(self, store):
        parts = store.pootle_path.strip("/").split("/")
        lang_code = parts[0]
        subdirs = parts[2:-1]
        filename = parts[-1]
        fs_path = None
        if subdirs:
            fs_path = self._match_config_path(
                subdirs[0], lang_code, subdirs[1:], filename)
        if not fs_path:
            fs_path = self._match_config_path(
                "default", lang_code, subdirs, filename)
        if fs_path:
            return "/%s" % fs_path.lstrip("/")

    def pull_translations(self, pootle_path=None, fs_path=None):
        status = self.status()
        for fs_file in (status['fs_added'] + status['fs_ahead']):
            if pootle_path:
                if not fnmatch(fs_file.pootle_path, pootle_path):
                    continue
            if fs_path:
                if not fnmatch(fs_file.path, fs_path):
                    continue
            fs_file.file.pull()

    def push_translations(self, pootle_path=None, fs_path=None):
        status = self.status()
        for fs_file in (status['pootle_added'] + status['pootle_ahead']):
            if pootle_path:
                if not fnmatch(fs_file.pootle_path, pootle_path):
                    continue
            if fs_path:
                if not fnmatch(fs_file.path, fs_path):
                    continue
            fs_file.file.push()

    def pull(self):
        pass

    def push(self):
        pass

    def read(self, path):
        self.pull()
        target = os.path.join(self.local_fs_path, path)
        with open(target) as f:
            content = f.read()
        return content

    def read_config(self):
        config = ConfigParser()
        config.readfp(io.BytesIO(self.read(self.fs.pootle_config)))
        return config

    def status(self):
        self.pull()
        return self.status_class(self)


class Plugins(object):

    def __init__(self):
        self.__plugins__ = {}

    def register(self, plugin):
        self.__plugins__[plugin.name] = plugin

    def __getitem__(self, k):
        return self.__plugins__[k]

    def __contains__(self, k):
        return k in self.__plugins__
