import os

from import_export.utils import import_file

from pootle_language.models import Language
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject


class FSFile(object):

    def __init__(self, fs_store):
        """
        :param pootle_path: Pootle path
        :param path: Path in FS of this file
        """
        self.fs_store = fs_store
        self.pootle_path = fs_store.pootle_path
        self.path = fs_store.path

    def __str__(self):
        return "<%s: %s::%s>" % (
            self.__name__, self.pootle_path, self.path)

    @property
    def file_path(self):
        return os.path.join(
            self.fs.plugin.local_fs_path,
            self.path.strip("/"))

    @property
    def exists(self):
        return os.path.exists(self.file_path)

    @property
    def filename(self):
        return self.pootle_path.split("/")[-1]

    @property
    def fs(self):
        return self.project.fs.get()

    @property
    def project(self):
        return self.fs_store.project

    @property
    def project_code(self):
        return self.pootle_path.split("/")[1]

    @property
    def language(self):
        if self.fs_store.store:
            return self.fs_store.store.translation_project.language
        return Language.objects.get(code=self.pootle_path.split("/")[2])

    @property
    def translation_project(self):
        if self.fs_store.store:
            return self.fs_store.store.translation_project
        try:
            return self.project.translationproject_set.get(
                language=self.language)
        except TranslationProject.DoesNotExist:
            return

    @property
    def directory_path(self):
        return '/'.join(self.pootle_path.split("/")[3:-1])

    @property
    def directory(self):
        if self.fs_store.store:
            return self.fs_store.store.parent
        if not self.translation_project:
            return
        directory = self.translation_project.directory
        if self.directory_path:
            for subdir in self.directory_path.split("/"):
                (directory,
                 created) = directory.child_dirs.get_or_create(name=subdir)
        return directory

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
    def latest_hash(self):
        raise NotImplementedError

    def fetch(self):
        fs_store = self.fs_store
        if self.store and not fs_store.store:
            fs_store.store = self.store
            fs_store.save()
        return fs_store

    def pull(self):
        with open(self.file_path) as f:
            import_file(
                f,
                pootle_path=self.pootle_path,
                rev=self.store.get_max_unit_revision())
        fs_store = self.fs_store
        fs_store.last_sync_hash = self.latest_hash
        fs_store.last_sync_revision = self.store.get_max_unit_revision()
        fs_store.save()

    def read(self):
        # self.fs.pull()
        with open(self.file_path) as f:
            return f.read()
