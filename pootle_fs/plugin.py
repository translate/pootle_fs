from ConfigParser import ConfigParser
from fnmatch import fnmatch
import io
import logging
import os
import shutil

from django.conf import settings
from django.core.files import File
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle_store.models import Store

from .files import FSFile
from .finder import TranslationFileFinder
from .language import LanguageMapper
from .models import FS_WINS, POOTLE_WINS
from .status import ProjectFSStatus, ActionResponse


logger = logging.getLogger(__name__)


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

    @property
    def addable_translations(self):
        for store in self.stores.filter(fs__isnull=True):
            fs_path = self.get_fs_path(store.pootle_path)
            if fs_path:
                yield store, fs_path

    @property
    def conflicting_translations(self):
        unresolved = self.synced_translations.filter(
            resolve_conflict__isnull=True)
        for translation in unresolved:
            fs_file = translation.file
            if fs_file.fs_changed and fs_file.pootle_changed:
                yield translation

    @property
    def is_cloned(self):
        if os.path.exists(self.local_fs_path):
            return True
        return False

    @cached_property
    def lang_mapper(self):
        return self.language_mapper_class(self)

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
        if not self.is_cloned:
            self.pull()

        response = self.response_class(self)
        status = self.status(pootle_path=pootle_path, fs_path=fs_path)
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
        if not self.is_cloned:
            self.pull()

        response = self.response_class(self)
        status = self.status(pootle_path=pootle_path, fs_path=fs_path)
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

        for section in config.sections():
            if section == "default":
                section_subdirs = []
            else:
                section_subdirs = section.split("/")

            finder = self.get_finder(
                config.get(section, "translation_path"))
            missing_langs = set()
            for file_path, matched in finder.find():
                path = file_path.replace(self.local_fs_path, "")
                if fs_path is not None:
                    if not fnmatch(path, fs_path):
                        continue
                language = self.lang_mapper.get_lang(matched['lang'])
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
                    + [matched.get("filename")
                       or os.path.basename(file_path)])
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
                translation_path))

    @lru_cache(maxsize=None)
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

    def merge_translations(self, pootle_path=None, fs_path=None,
                           response=None, status=None, pootle_wins=False):
        """
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        """
        from .models import StoreFS

        status = self.status(pootle_path=pootle_path, fs_path=fs_path)
        response = self.response_class(self)

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

    def merge_translation_files(self, pootle_path=None, fs_path=None,
                                response=None, status=None):
        if response is None:
            response = self.response_class(self)
        if status is None:
            status = self.status(pootle_path=pootle_path, fs_path=fs_path)
        for fs_status in status["merge_pootle"]:
            fs_status.store_fs.file.sync_to_pootle(
                merge=True, pootle_wins=True)
            fs_status.store_fs.file.sync_from_pootle()
            response.add("merged_from_pootle", fs_status)
        for fs_status in status["merge_fs"]:
            fs_status.store_fs.file.sync_to_pootle(
                merge=True, pootle_wins=False)
            fs_status.store_fs.file.sync_from_pootle()
            response.add("merged_from_fs", fs_status)

    def pull(self):
        """
        Pull the FS from external source if required.
        """
        pass

    def pull_translations(self, pootle_path=None, fs_path=None,
                          response=None, status=None):
        """
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        """
        if response is None:
            response = self.response_class(self)
        if status is None:
            status = self.status(pootle_path=pootle_path, fs_path=fs_path)
        for fs_status in (status['fs_added'] + status['fs_ahead']):
            fs_status.store_fs.file.pull()
            response.add("pulled_to_pootle", fs_status)
        return response

    def push(self, paths=None, message=None):
        """
        Push the FS to an external source if required.
        """
        pass

    def push_translations(self, pootle_path=None,
                          fs_path=None, status=None, response=None):
        if response is None:
            response = self.response_class(self)
        self.push_translation_files(
            status=status, pootle_path=pootle_path,
            fs_path=fs_path, response=response)
        for action_status in response.completed("pushed_to_fs"):
            fs_file = action_status.store_fs.file
            fs_file.on_sync(
                fs_file.latest_hash,
                action_status.store_fs.store.get_max_unit_revision())
        self.push(response)
        return response

    def push_translation_files(self, pootle_path=None,
                               fs_path=None, status=None, response=None):
        """
        :param prune: Remove files that do not exist in Pootle.
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        """
        if response is None:
            response = self.response_class(self)
        if status is None:
            status = self.status(pootle_path=pootle_path, fs_path=fs_path)
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
        self.read_config.cache_clear()
        self.fs.current_config.save(
            self.fs.pootle_config,
            File(io.BytesIO(self.read(self.fs.pootle_config))))

    @lru_cache(maxsize=None)
    def read_config(self):
        """
        Read and parse the configuration for this project

        :return config: Where ``config`` is an ``ConfigParser`` instance
        """
        config = ConfigParser()
        if not self.fs.current_config:
            self.update_config()
        config.readfp(io.BytesIO(self.fs.current_config.file.read()))
        return config

    def status(self, fs_path=None, pootle_path=None):
        """
        Get a status object for showing current status of FS/Pootle

        :return status: Where ``status`` is an instance of self.status_class
        """
        self.pull()
        return self.status_class(
            self, fs_path=fs_path, pootle_path=pootle_path)

    def remove_file(self, path):
        os.unlink(
            os.path.join(
                self.local_fs_path, path.strip("/")))

    def rm_translations(self, pootle_path=None, fs_path=None):
        """
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        """
        from .models import StoreFS

        status = self.status(pootle_path=pootle_path, fs_path=fs_path)
        response = self.response_class(self)
        untracked = (
            status["fs_untracked"] + status["pootle_untracked"]
            + status["conflict_untracked"])

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

    def remove_translation_files(self, pootle_path=None,
                                 fs_path=None, status=None, response=None):
        """
        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        """
        if response is None:
            response = self.response_class(self)
        if status is None:
            status = self.status(pootle_path=pootle_path, fs_path=fs_path)
        for fs_status in status['to_remove']:
            fs_status.store_fs.file.delete()
            response.add("removed", fs_status)

    def sync_translations(self, pootle_path=None, fs_path=None):
        response = self.response_class(self)
        status = self.status(pootle_path=pootle_path, fs_path=fs_path)
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
