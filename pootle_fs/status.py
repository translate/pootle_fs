import os

from .models import FS_WINS, POOTLE_WINS


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
    def store_fs_paths(self):
        if not self.__cached__['store_fs_paths']:
            self.__cached__['store_fs_paths'] = (
                self.fs.translations.values_list(
                    "pootle_path", flat=True))
        return self.__cached__['store_fs_paths']

    @property
    def store_paths(self):
        if not self.__cached__['store_paths']:
            self.__cached__['store_paths'] = (
                self.fs.stores.values_list(
                    "pootle_path", flat=True))
        return self.__cached__['store_paths']

    @property
    def fs_translations(self):
        if not self.__cached__['fs_translations']:
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
        for pootle_path, path in self.fs_translations:
            if pootle_path in self.store_fs_paths:
                continue
            if pootle_path in self.store_paths:
                yield self.link_status_class(
                    "conflict_untracked",
                    pootle_path=pootle_path,
                    fs_path=path)

    def get_fs_untracked(self):
        for pootle_path, path in self.fs_translations:
            exists_anywhere = (
                pootle_path in self.store_fs_paths
                or pootle_path in self.store_paths)
            if exists_anywhere:
                continue
            yield self.link_status_class(
                "fs_untracked",
                pootle_path=pootle_path,
                fs_path=path)

    def get_pootle_untracked(self):
        for store, path in self.addable_translations:
            target = os.path.join(
                self.fs.local_fs_path,
                self.fs.get_fs_path(store).lstrip("/"))
            if not os.path.exists(target):
                yield self.link_status_class(
                    "pootle_untracked",
                    store=store,
                    fs_path=path)

    def get_pootle_added(self):
        for store_fs in self.unsynced_translations:
            if store_fs.store:
                if not store_fs.resolve_conflict == FS_WINS:
                    yield self.link_status_class(
                        "pootle_added",
                        store_fs=store_fs)

    def get_fs_added(self):
        for store_fs in self.unsynced_translations:
            if store_fs.file.exists:
                if not store_fs.resolve_conflict == POOTLE_WINS:
                    yield self.link_status_class(
                        "fs_added",
                        store_fs=store_fs)

    def get_fs_removed(self):
        for store_fs in self.synced_translations:
            if not store_fs.file.exists and store_fs.store:
                yield self.link_status_class(
                    "fs_removed",
                    store_fs=store_fs)

    def get_pootle_removed(self):
        for store_fs in self.synced_translations:
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

    def __init__(self, fs):
        self.fs = fs
        self.check_status()

    def check_status(self):
        caches = [
            "fs_translations",
            "store_paths",
            "store_fs_paths",
            "addable_translations",
            "unsynced_translations",
            "synced_translations"]
        self.__cached__ = {k: None for k in caches}
        self.__cached__["changes"] = {}
        stati = [
            "conflict",
            "conflict_untracked",
            "fs_added",
            "fs_ahead",
            "fs_untracked",
            "fs_removed",
            "pootle_ahead",
            "pootle_untracked",
            "pootle_added",
            "pootle_removed"]
        self.__status__ = {k: [] for k in stati}
        for k in stati:
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
