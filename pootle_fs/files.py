import os
from datetime import datetime

# from import_export.utils import import_file


from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject


class FSFile(object):

    def __init__(self, fs_store):
        """
        :param fs_store: ``FSStore`` object
        """
        from .models import StoreFS
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
        return Language.objects.get(code=self.pootle_path.split("/")[1])

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
                try:
                    directory = directory.child_dirs.get(name=subdir)
                except Directory.DoesNotExist:
                    return
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
    def fs_changed(self):
        latest_hash = self.latest_hash
        return (
            latest_hash
            and (
                latest_hash
                != self.fs_store.last_sync_hash))

    @property
    def pootle_changed(self):
        return (
            self.store
            and (
                self.store.get_max_unit_revision()
                != self.fs_store.last_sync_revision))

    @property
    def latest_hash(self):
        raise NotImplementedError

    def create_store(self):
        if not self.translation_project:
            TranslationProject.objects.create(
                project=self.project,
                language=self.language)
        if not self.directory:
            directory = self.translation_project.directory
            if self.directory_path:
                for subdir in self.directory_path.split("/"):
                    directory, created = directory.child_dirs.get_or_create(
                        name=subdir)
        if not self.store:
            store, created = Store.objects.get_or_create(
                parent=self.directory, name=self.filename,
                translation_project=self.translation_project)
        if not self.fs_store.store == self.store:
            self.fs_store.store = self.store
            self.fs_store.save()

    def fetch(self):
        if self.store and not self.fs_store.store:
            self.fs_store.store = self.store
            self.fs_store.save()
        return self.fs_store

    def on_sync(self, latest_hash, revision):
        self.fs_store.resolve_conflict = None
        self.fs_store.last_sync_hash = latest_hash
        self.fs_store.last_sync_revision = revision
        self.fs_store.save()

    def sync_to_pootle(self):
        # with open(self.file_path) as f:
        #    import_file(
        #        f,
        #        pootle_path=self.pootle_path,
        #        rev=self.store.get_max_unit_revision())
        self.on_sync(
            self.latest_hash,
            self.store.get_max_unit_revision())

    def sync_from_pootle(self):
        with open(self.file_path, "w") as f:
            f.write(str(datetime.now()))
        self.on_sync(
            self.latest_hash,
            self.store.get_max_unit_revision())

    def pull(self):
        if not self.store:
            self.create_store()
        if not self.fs_store.store == self.store:
            self.fs_store.store = self.store
            self.fs_store.save()
        self.sync_to_pootle()

    def push(self):
        # TODO: check that store exists!
        current_revision = self.store.get_max_unit_revision()
        last_revision = self.fs_store.last_sync_revision
        if last_revision and (last_revision == current_revision):
            return
        directory = os.path.dirname(self.fs_store.file.file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.sync_from_pootle()

    def read(self):
        # self.fs.pull()
        with open(self.file_path) as f:
            return f.read()
