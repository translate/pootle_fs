from collections import OrderedDict
from fnmatch import fnmatch
import os

from .models import FS_WINS, POOTLE_WINS


FS_STATUS = OrderedDict()
FS_STATUS["conflict"] = {
    "title": "Conflicts",
    "description": "Both Pootle Store and file in filesystem have changed"}
FS_STATUS["conflict_untracked"] = {
    "title": "Untracked conflicts",
    "description": (
        "Newly created files in the filesystem matching newly created Stores "
        "in Pootle")}
FS_STATUS["pootle_ahead"] = {
    "title": "Changed in Pootle",
    "description": "Stores that have changed in Pootle"}
FS_STATUS["pootle_untracked"] = {
    "title": "Untracked Stores",
    "description": "Newly created Stores in Pootle"}
FS_STATUS["pootle_added"] = {
    "title": "Added in Pootle",
    "description": (
        "Stores that have been added in Pootle and are now being tracked")}
FS_STATUS["pootle_removed"] = {
    "title": "Removed from Pootle",
    "description": "Stores that have been removed from Pootle"}
FS_STATUS["fs_added"] = {
    "title": "Fetched from filesystem",
    "description": (
        "Files that have been fetched from the filesystem and are now being "
        "tracked")}
FS_STATUS["fs_ahead"] = {
    "title": "Changed in filesystem",
    "description": "A file has been changed in the filesystem"}
FS_STATUS["fs_untracked"] = {
    "title": "Untracked files",
    "description": "Newly created files in the filesystem"}
FS_STATUS["fs_removed"] = {
    "title": "Removed from filesystem",
    "description": "Files that have been removed from the filesystem"}


class Status(object):

    def __init__(self, status, store_fs=None, store=None,
                 fs_path=None, pootle_path=None):
        self.store_fs = store_fs
        self.store = store
        self.fs_path = fs_path
        self.pootle_path = pootle_path
        if store_fs:
            self.fs_path = store_fs.path
            self.pootle_path = store_fs.pootle_path
        elif store:
            self.pootle_path = store.pootle_path

        if not self.fs_path or not self.pootle_path:
            raise ValueError(
                "Status class requires fs_path and pootle_path to be set")


class ProjectFSStatus(object):

    link_status_class = Status

    @property
    def store_fs_pootle_paths(self):
        if not self.__cached__['store_fs_pootle_paths']:
            self.__cached__['store_fs_pootle_paths'] = (
                self.fs.translations.values_list(
                    "pootle_path", flat=True))
        return self.__cached__['store_fs_pootle_paths']

    @property
    def store_paths(self):
        if not self.__cached__['store_paths']:
            self.__cached__['store_paths'] = (
                self.fs.stores.values_list(
                    "pootle_path", flat=True))
        return self.__cached__['store_paths']

    @property
    def store_reversed_paths(self):
        if not self.__cached__['store_paths']:
            self.__cached__['store_paths'] = {
                self.fs.get_fs_path(pootle_path): pootle_path
                for pootle_path
                in self.fs.stores.values_list("pootle_path", flat=True)}
        return self.__cached__['store_paths']

    @property
    def store_fs_paths(self):
        if not self.__cached__['store_fs_paths']:
            self.__cached__['store_fs_paths'] = (
                self.fs.translations.values_list(
                    "path", flat=True))
        return self.__cached__['store_fs_paths']

    @property
    def fs_translations(self):
        if self.__cached__['fs_translations'] is None:
            self.__cached__['fs_translations'] = [
                t for t in self.fs.find_translations()]
        return self.__cached__['fs_translations']

    @property
    def addable_translations(self):
        if not self.__cached__['addable_translations']:
            self.__cached__['addable_translations'] = (
                self.fs.addable_translations)
        return self.__cached__['addable_translations']

    @property
    def unsynced_translations(self):
        if not self.__cached__['unsynced_translations']:
            self.__cached__['unsynced_translations'] = (
                self.fs.unsynced_translations)
        return self.__cached__['unsynced_translations']

    @property
    def synced_translations(self):
        if not self.__cached__['synced_translations']:
            self.__cached__['synced_translations'] = (
                self.fs.synced_translations)
        return self.__cached__['synced_translations']

    def get_conflict_untracked(self):
        reversed_paths = self.store_reversed_paths
        for pootle_path, path in self.fs_translations:
            if self._filtered(pootle_path, path):
                continue
            if pootle_path in self.store_fs_pootle_paths:
                continue
            if path in self.store_fs_paths:
                continue
            conflicts = False
            if pootle_path in self.store_paths:
                conflicts = True
            elif path in reversed_paths:
                pootle_path = reversed_paths[path]
                conflicts = True
            if conflicts:
                # print("Yielding conflict_untracked status")
                yield self.link_status_class(
                    "conflict_untracked",
                    pootle_path=pootle_path,
                    fs_path=path)

    def get_fs_untracked(self):
        reversed_paths = self.store_reversed_paths
        for pootle_path, path in self.fs_translations:
            if self._filtered(pootle_path, path):
                continue
            exists_anywhere = (
                pootle_path in self.store_fs_pootle_paths
                or pootle_path in self.store_paths
                or path in self.store_fs_paths
                or path in reversed_paths)
            if exists_anywhere:
                continue
            yield self.link_status_class(
                "fs_untracked",
                pootle_path=pootle_path,
                fs_path=path)

    def get_pootle_untracked(self):
        for store, path in self.addable_translations:
            if self._filtered(store.pootle_path, path):
                continue
            target = os.path.join(
                self.fs.local_fs_path,
                self.fs.get_fs_path(store.pootle_path).lstrip("/"))
            if not os.path.exists(target):
                yield self.link_status_class(
                    "pootle_untracked",
                    store=store,
                    fs_path=path)

    def get_pootle_added(self):
        for store_fs in self.unsynced_translations:
            if self._filtered(store_fs.pootle_path, store_fs.path):
                continue
            if store_fs.store:
                if not store_fs.resolve_conflict == FS_WINS:
                    yield self.link_status_class(
                        "pootle_added",
                        store_fs=store_fs)

    def _filtered(self, pootle_path, fs_path):
        return (
            (self.pootle_path
             and not fnmatch(pootle_path, self.pootle_path))
            or
            (self.fs_path
             and not fnmatch(fs_path, self.fs_path)))

    def get_fs_added(self):
        for store_fs in self.unsynced_translations:
            if self._filtered(store_fs.pootle_path, store_fs.path):
                continue

            if store_fs.file.exists:
                if not store_fs.resolve_conflict == POOTLE_WINS:
                    yield self.link_status_class(
                        "fs_added",
                        store_fs=store_fs)

    def get_fs_removed(self):
        for store_fs in self.synced_translations:
            if self._filtered(store_fs.pootle_path, store_fs.path):
                continue
            if not store_fs.file.exists and store_fs.store:
                yield self.link_status_class(
                    "fs_removed",
                    store_fs=store_fs)

    def get_pootle_removed(self):
        for store_fs in self.synced_translations:
            if self._filtered(store_fs.pootle_path, store_fs.path):
                continue
            if store_fs.file.exists and not store_fs.store:
                yield self.link_status_class(
                    "pootle_removed",
                    store_fs=store_fs)

    def get_both_removed(self):
        for store_fs in self.synced_translations:
            if not store_fs.file.exists and not store_fs.store:
                yield self.link_status_class(
                    "both_removed",
                    store_fs=store_fs)

    def _get_changes(self, store_fs):
        if store_fs.pk in self.__cached__['changes']:
            return self.__cached__['changes'][store_fs.pk]
        fs_file = store_fs.file
        self.__cached__['changes'][store_fs.pk] = (
            fs_file.pootle_changed, fs_file.fs_changed)
        return self.__cached__['changes'][store_fs.pk]

    def get_fs_ahead(self):
        for store_fs in self.synced_translations:
            pootle_changed, fs_changed = self._get_changes(store_fs)
            if fs_changed:
                if not pootle_changed or store_fs.resolve_conflict == FS_WINS:
                    yield self.link_status_class(
                        "fs_ahead",
                        store_fs=store_fs)

    def get_pootle_ahead(self):
        for store_fs in self.synced_translations:
            pootle_changed, fs_changed = self._get_changes(store_fs)
            if pootle_changed:
                if not fs_changed or store_fs.resolve_conflict == POOTLE_WINS:
                    yield self.link_status_class(
                        "pootle_ahead",
                        store_fs=store_fs)

    def get_conflict(self):
        for store_fs in self.synced_translations:
            pootle_changed, fs_changed = self._get_changes(store_fs)
            if fs_changed and pootle_changed and not store_fs.resolve_conflict:
                yield self.link_status_class(
                    "conflict",
                    store_fs=store_fs)

    def get_up_to_date(self):
        problem_paths = []
        for k, v in self.__status__.items():
            if v:
                problem_paths += [p.pootle_path for p in v]
        return self.synced_translations.exclude(
            pootle_path__in=problem_paths)

    def __init__(self, fs, fs_path=None, pootle_path=None):
        self.fs = fs
        self.check_status(fs_path=fs_path, pootle_path=pootle_path)

    def check_status(self, fs_path=None, pootle_path=None):
        self.fs_path = fs_path
        self.pootle_path = pootle_path
        # print("Checking status")
        caches = [
            "fs_translations",
            "store_paths",
            "store_fs_paths",
            "store_fs_pootle_paths",
            "addable_translations",
            "unsynced_translations",
            "synced_translations"]
        self.__cached__ = {k: None for k in caches}
        self.__cached__["changes"] = {}
        self.__status__ = {k: [] for k in FS_STATUS.keys()}
        for k in FS_STATUS.keys():
            # print("Checking %s" % k)
            for v in getattr(self, "get_%s" % k)():
                self.add(k, v)
        return self

    def __getitem__(self, k):
        return self.__status__[k]

    def __contains__(self, k):
        return k in self.__status__ and self.__status__[k]

    def __iter__(self):
        for k in self.__status__:
            if self.__status__[k]:
                yield k

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
            self.__status__[k].append(v)
