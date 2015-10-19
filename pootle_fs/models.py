from django.db import models
from django.utils.functional import cached_property

from pootle_project.models import Project
from pootle_store.models import Store

from .exceptions import MissingPluginError
from .managers import (
    ProjectFSManager, validate_project_fs,
    StoreFSManager, validate_store_fs)


POOTLE_WINS = 1
FS_WINS = 2


class StoreFS(models.Model):
    project = models.ForeignKey(
        Project, related_name='store_fs')
    pootle_path = models.CharField(max_length=255, blank=False)
    path = models.CharField(max_length=255, blank=False)
    store = models.ForeignKey(
        Store, related_name='fs', blank=True, null=True,
        on_delete=models.SET_NULL)
    last_sync_revision = models.IntegerField(blank=True, null=True)
    last_sync_mtime = models.DateTimeField(null=True, blank=True)
    last_sync_hash = models.CharField(max_length=64, blank=True, null=True)
    staged_for_removal = models.BooleanField(default=False)
    staged_for_merge = models.BooleanField(default=False)
    resolve_conflict = models.IntegerField(
        blank=True, null=True,
        default=0,
        choices=[(0, ""),
                 (POOTLE_WINS, "pootle"),
                 (FS_WINS, "fs")])

    objects = StoreFSManager()

    @property
    def file(self):
        return self.fs.fs_file(self)

    @cached_property
    def fs(self):
        return self.project.fs.get()

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
    current_config = models.FileField(blank=True, null=True)

    objects = ProjectFSManager()

    @cached_property
    def plugin(self):
        from pootle_fs import plugins
        try:
            return plugins[self.fs_type](self)
        except KeyError:
            raise MissingPluginError(
                "No such plugin: %s" % self.fs_type)

    def fs_file(self, fs_store):
        return self.plugin.file_class(fs_store)

    def save(self, *args, **kwargs):
        validate_project_fs(
            fs_type=self.fs_type)
        return super(ProjectFS, self).save(*args, **kwargs)
