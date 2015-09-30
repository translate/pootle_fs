from django.db import models

from pootle_project.models import Project
from pootle_store.models import Store

from .exceptions import MissingPluginError
from .managers import (
    ProjectFSManager, validate_project_fs,
    StoreFSManager, validate_store_fs)


class StoreFS(models.Model):
    project = models.ForeignKey(
        Project, related_name='store_fs')
    pootle_path = models.CharField(max_length=255, blank=False)
    path = models.CharField(max_length=255, blank=False)
    store = models.ForeignKey(Store, related_name='fs', blank=True, null=True)
    last_sync_revision = models.IntegerField(blank=True, null=True)
    last_sync_mtime = models.DateTimeField(null=True, blank=True)
    last_sync_hash = models.CharField(max_length=32, blank=True, null=True)

    objects = StoreFSManager()

    @property
    def fs(self):
        return self.project.fs.get()

    @property
    def file(self):
        return self.fs.fs_file(self)

    def save(self, *args, **kwargs):
        validated = validate_store_fs(
            store=self.store,
            project=self.project,
            pootle_path=self.pootle_path,
            path=self.path)
        self.store = validated.get("store")
        self.project = validated.get("project")
        self.pootle_path = validated.get("pootle_path")
        self.path = validated.get("path")
        return super(StoreFS, self).save(*args, **kwargs)


class ProjectFS(models.Model):
    project = models.ForeignKey(
        Project, related_name='fs', unique=True)
    url = models.URLField()
    fs_type = models.CharField(max_length=32)
    enabled = models.BooleanField(default=True)
    fetch_frequency = models.IntegerField(default=0)
    push_frequency = models.IntegerField(default=0)
    pootle_config = models.CharField(max_length=32, default=".pootle.ini")

    objects = ProjectFSManager()

    def save(self, *args, **kwargs):
        validate_project_fs(
            fs_type=self.fs_type)
        return super(ProjectFS, self).save(*args, **kwargs)

    @property
    def plugin(self):
        from pootle_fs import plugins
        try:
            return plugins[self.fs_type](self)
        except KeyError:
            raise MissingPluginError(
                "No such plugin: %s" % self.fs_type)

    ###########################
    # FS Plugin implementation

    def fs_file(self, fs_store):
        return self.plugin.file_class(fs_store)

    def pull(self):
        return self.plugin.pull()

    def get_latest_hash(self):
        return self.plugin.get_latest_hash()

    def fetch_translations(self):
        return self.plugin.fetch_translations()

    def list_translations(self):
        return self.plugin.translations

    def pull_translations(self):
        return self.plugin.pull_translations()

    def read_config(self):
        return self.plugin.read_config()

    def status(self):
        return self.plugin.status()

    # FS Plugin implementation
    ###########################
