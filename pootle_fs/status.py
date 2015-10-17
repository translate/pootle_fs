from collections import OrderedDict
from fnmatch import fnmatch
import logging
import re
import os

from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle_store.models import Store

from .models import FS_WINS, POOTLE_WINS, StoreFS


logger = logging.getLogger(__name__)

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
FS_STATUS["merge_pootle"] = {
    "title": "Staged for merge (Pootle wins)",
    "description": (
        "Files or Stores that have been staged for merging on sync - pootle "
        "wins where units are both updated")}
FS_STATUS["merge_fs"] = {
    "title": "Staged for merge (FS wins)",
    "description": (
        "Files or Stores that have been staged for merging on sync - FS "
        "wins where units are both updated")}
FS_STATUS["to_remove"] = {
    "title": "Staged for removal",
    "description": "Files or Stores that have been staged or removal on sync"}

FS_ACTION = OrderedDict()
FS_ACTION["pruned_from_pootle"] = {
    "title": "Deleted in Pootle",
    "description":
        "Stores removed from Pootle that were not present in the filesystem"}
FS_ACTION["pulled_to_pootle"] = {
    "title": "Pulled to Pootle",
    "description":
        "Stores updated where filesystem version was new or newer"}
FS_ACTION["added_from_pootle"] = {
    "title": "Added from Pootle",
    "description":
        "Files staged from Pootle that were new or newer than their files"}
FS_ACTION["pruned_from_fs"] = {
    "title": "Pruned from filesystem",
    "description":
        ("Files removed from the filesystem that did not have matching Pootle "
         "Stores")}
FS_ACTION["fetched_from_fs"] = {
    "title": "Fetched from filesystem",
    "description":
        ("Files staged from the filesystem that were new or newer than their "
         "Pootle Stores")}
FS_ACTION["pushed_to_fs"] = {
    "title": "Pushed to filesystem",
    "description":
        "Files updated where Pootle Store version was new or newer"}
FS_ACTION["staged_for_removal"] = {
    "title": "Staged for removal",
    "description":
        ("Files or Stores staged for removal where the corresponding "
         "file/Store is missing")}
FS_ACTION["removed"] = {
    "title": "Removed",
    "description":
        ("Files or Stores removed that no longer had corresponding files or "
         "Stores")}
FS_ACTION["staged_for_merge_fs"] = {
    "title": "Staged for merge (FS Wins)",
    "description":
        ("Files or Stores staged for merge where the corresponding "
         "file/Store has also been updated or created")}
FS_ACTION["staged_for_merge_pootle"] = {
    "title": "Staged for merge (Pootle Wins)",
    "description":
        ("Files or Stores staged for merge where the corresponding "
         "file/Store has also been updated or created")}
FS_ACTION["merged_from_fs"] = {
    "title": "Merged from fs",
    "description":
        ("Merged - FS won where unit updates conflicted")}
FS_ACTION["merged_from_pootle"] = {
    "title": "Merged from pootle",
    "description":
        ("Merged - Pootle won where unit updates conflicted")}


class Status(object):

    def __init__(self, status, store_fs=None, store=None,
                 fs_path=None, pootle_path=None):
        self.status = status
        self.store_fs = store_fs
        self.store = store
        self.fs_path = fs_path
        self.pootle_path = pootle_path
        self._set_paths()

    def __eq__(self, other):
        eq = (
            isinstance(other, self.__class__)
            and other.status == self.status
            and other.store_fs == self.store_fs
            and other.store == self.store
            and other.fs_path == self.fs_path
            and other.pootle_path == self.pootle_path)
        return eq

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.pootle_path > other.pootle_path
        return super(Status, self).__gt__(other)

    def _set_paths(self):
        if self.store_fs:
            self.fs_path = self.store_fs.path
            self.pootle_path = self.store_fs.pootle_path
        elif self.store:
            self.pootle_path = self.store.pootle_path

        if not self.fs_path or not self.pootle_path:
            raise ValueError(
                "Status class requires fs_path and pootle_path to be set")


class ActionStatus(Status):

    def __init__(self, action_type, original_status, complete=True, msg=None):
        self.action_type = action_type
        self.complete = complete
        self.original_status = original_status

    @property
    def failed(self):
        return not self.complete

    @property
    def fs_path(self):
        return self.original_status.fs_path

    @property
    def pootle_path(self):
        return self.original_status.pootle_path

    @property
    def store(self):
        if self.original_status.store:
            return self.original_status.store
        try:
            return Store.objects.get(
                pootle_path=self.original_status.pootle_path)
        except Store.DoesNotExist:
            return None

    @property
    def store_fs(self):
        if self.original_status.store_fs:
            return self.original_status.store_fs
        try:
            return StoreFS.objects.get(
                pootle_path=self.original_status.pootle_path,
                fs_path=self.original_status.fs_path)
        except:
            return None


class ActionResponse(object):

    __actions__ = None

    def __init__(self, plugin):
        self.plugin = plugin
        self.__actions__ = {}
        for k in FS_ACTION.keys():
            self.__actions__[k] = []
            self.__actions__[k] = []

    def __getitem__(self, k):
        return self.__actions__[k]

    def __iter__(self):
        for k in self.__actions__:
            if self.__actions__[k]:
                yield k

    def __len__(self):
        return len([x for x in self.__iter__()])

    def __str__(self):
        if self.made_changes:
            return (
                "<FSActionResponse(%s): %s>"
                % (self.plugin.project,
                   ', '.join(["%s: %s" % (k, len(v))
                              for k, v in self.__actions__.items()
                              if v])))
        return "<FSActionResponse(%s): No changes made>" % self.plugin.project

    @property
    def action_types(self):
        return FS_ACTION.keys()

    @property
    def has_failed(self):
        return len(list(self.failed())) and True or False

    @property
    def made_changes(self):
        for complete in self.completed():
            return True
        return False

    def add(self, action_type, fs_status, complete=True, msg=None):
        action = ActionStatus(
            action_type, fs_status, complete=complete, msg=msg)
        self.__actions__[action_type].append(action)
        return action

    def completed(self, *action_types):
        action_types = action_types or self.action_types
        for action_type in action_types:
            for action in self.__actions__[action_type]:
                if not action.failed:
                    yield action

    def failed(self, *action_types):
        action_types = action_types or self.action_types
        for action_type in action_types:
            for action in self.__actions__[action_type]:
                if action.failed:
                    yield action

    def get_action_description(self, action_type, failures=False):
        return self.get_action_type(action_type)["description"]

    def get_action_title(self, action_type, failures=False):
        st_type = self.get_action_type(action_type)
        return (
            "%s (%s)"
            % (st_type['title'],
               len(list(self.completed()))))

    def get_action_type(self, action_type):
        return FS_ACTION[action_type]


class ProjectFSStatus(object):

    link_status_class = Status

    def __init__(self, fs, fs_path=None, pootle_path=None):
        self.fs = fs
        self.__status__ = {}
        self._check_status(fs_path=fs_path, pootle_path=pootle_path)

    def __contains__(self, k):
        return k in self.__status__ and self.__status__[k]

    def __getitem__(self, k):
        return self.__status__[k]

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

    @cached_property
    def addable_translations(self):
        return self.fs.addable_translations

    @cached_property
    def fs_path_root(self):
        return self._path_root.sub("", self.fs_path)

    @cached_property
    def fs_translations(self):
        return sorted([t for t in self.fs.find_translations()])

    @property
    def has_changed(self):
        return any(self.__status__.values())

    @cached_property
    def pootle_path_root(self):
        return self._path_root.sub("", self.pootle_path)

    @cached_property
    def store_fs_paths(self):
        return self.fs.translations.values_list("path", flat=True)

    @cached_property
    def store_fs_pootle_paths(self):
        return self.fs.translations.values_list("pootle_path", flat=True)

    @cached_property
    def store_paths(self):
        return self.fs.stores.values_list("pootle_path", flat=True)

    @cached_property
    def store_reversed_paths(self):
        return {
            self.fs.get_fs_path(pootle_path): pootle_path
            for pootle_path
            in self.fs.stores.values_list("pootle_path", flat=True)}

    @cached_property
    def synced_translations(self):
        synced = self.fs.synced_translations.exclude(
            staged_for_removal=True).exclude(staged_for_merge=True)
        if self.pootle_path:
            synced = synced.filter(
                pootle_path__startswith=self.pootle_path_root)
        if self.fs_path:
            synced = synced.filter(
                path__startswith=self.fs_path_root)
        return synced

    @cached_property
    def unsynced_translations(self):
        unsynced = self.fs.unsynced_translations.exclude(
            staged_for_removal=True).exclude(staged_for_merge=True)
        if self.pootle_path:
            unsynced = unsynced.filter(
                pootle_path__startswith=self.pootle_path_root)
        if self.fs_path:
            unsynced = unsynced.filter(
                path__startswith=self.fs_path_root)
        return unsynced

    @cached_property
    def _path_root(self):
        return re.compile("[\?\[\*].*")

    def add(self, k, v):
        if k in self.__status__:
            self.__status__[k].append(v)

    def check_status(self, fs_path=None, pootle_path=None):
        self.fs.pull()
        return self._check_status(
            fs_path=fs_path, pootle_path=pootle_path)

    def get_both_removed(self):
        for store_fs in self._filtered_qs(self.synced_translations):
            if not store_fs.file.exists and not store_fs.store:
                yield self.link_status_class(
                    "both_removed",
                    store_fs=store_fs)

    def get_conflict(self):
        for store_fs in self._filtered_qs(self.synced_translations):
            pootle_changed, fs_changed = self._get_changes(store_fs)
            if fs_changed and pootle_changed and not store_fs.resolve_conflict:
                yield self.link_status_class(
                    "conflict",
                    store_fs=store_fs)

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

    def get_fs_added(self):
        unsynced = self._filtered_qs(
            self.unsynced_translations.exclude(
                resolve_conflict=POOTLE_WINS))
        for store_fs in unsynced:
            if store_fs.file.exists:
                yield self.link_status_class(
                    "fs_added",
                    store_fs=store_fs)
        synced = self._filtered_qs(
            self.synced_translations.filter(
                resolve_conflict=FS_WINS))
        for store_fs in synced:
            if not store_fs.store and store_fs.file.exists:
                yield self.link_status_class(
                    "fs_added",
                    store_fs=store_fs)

    def get_fs_ahead(self):
        for store_fs in self._filtered_qs(self.synced_translations):
            pootle_changed, fs_changed = self._get_changes(store_fs)
            if fs_changed:
                if not pootle_changed or store_fs.resolve_conflict == FS_WINS:
                    yield self.link_status_class(
                        "fs_ahead",
                        store_fs=store_fs)

    def get_fs_removed(self):
        synced = self._filtered_qs(
            self.synced_translations.exclude(
                resolve_conflict=POOTLE_WINS))
        for store_fs in synced:
            if not store_fs.file.exists and store_fs.store:
                yield self.link_status_class(
                    "fs_removed",
                    store_fs=store_fs)

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

    def get_merge_pootle(self):
        to_merge = self.fs.translations.filter(
            staged_for_merge=True, resolve_conflict=POOTLE_WINS)

        for store_fs in self._filtered_qs(to_merge):
            yield self.link_status_class("merge_pootle", store_fs=store_fs)

    def get_merge_fs(self):
        to_merge = self.fs.translations.filter(
            staged_for_merge=True, resolve_conflict=FS_WINS)

        for store_fs in self._filtered_qs(to_merge):
            yield self.link_status_class("merge_fs", store_fs=store_fs)

    def get_pootle_added(self):
        unsynced = self._filtered_qs(
            self.unsynced_translations.exclude(
                resolve_conflict=FS_WINS))
        for store_fs in unsynced:
            if store_fs.store:
                yield self.link_status_class(
                    "pootle_added",
                    store_fs=store_fs)
        synced = self._filtered_qs(
            self.synced_translations.filter(
                resolve_conflict=POOTLE_WINS))
        for store_fs in synced:
            if not store_fs.file.exists and store_fs.store:
                yield self.link_status_class(
                    "pootle_added",
                    store_fs=store_fs)

    def get_pootle_ahead(self):
        for store_fs in self._filtered_qs(self.synced_translations):
            pootle_changed, fs_changed = self._get_changes(store_fs)
            if pootle_changed:
                if not fs_changed or store_fs.resolve_conflict == POOTLE_WINS:
                    yield self.link_status_class(
                        "pootle_ahead",
                        store_fs=store_fs)

    def get_pootle_removed(self):
        synced = self._filtered_qs(
            self.synced_translations.exclude(
                resolve_conflict=FS_WINS))
        for store_fs in synced:
            if store_fs.file.exists and not store_fs.store:
                yield self.link_status_class(
                    "pootle_removed",
                    store_fs=store_fs)

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

    def get_status_description(self, status_type):
        return self.get_status_type(status_type)['description']

    def get_status_title(self, status_type):
        st_type = self.get_status_type(status_type)
        return (
            "%s (%s)"
            % (st_type['title'], len(self[status_type])))

    def get_status_type(self, status_type):
        return FS_STATUS[status_type]

    def get_to_remove(self):
        to_remove = self.fs.translations.filter(staged_for_removal=True)

        for store_fs in self._filtered_qs(to_remove):
            yield self.link_status_class("to_remove", store_fs=store_fs)

    def get_up_to_date(self):
        problem_paths = []
        for k, v in self.__status__.items():
            if v:
                problem_paths += [p.pootle_path for p in v]
        return self.synced_translations.exclude(
            pootle_path__in=problem_paths)

    def _check_status(self, fs_path=None, pootle_path=None):
        self.fs_path = fs_path
        self.pootle_path = pootle_path
        self._clear_cache()
        logger.debug("Checking status")
        for k in FS_STATUS.keys():
            logger.debug("Checking %s" % k)
            for v in getattr(self, "get_%s" % k)():
                self.add(k, v)
        return self

    def _clear_cache(self):
        for k in self.__dict__.keys():
            if callable(getattr(self, k, None)):
                del self.__dict__[k]
        self._get_changes.cache_clear()
        self._filtered.cache_clear()
        self.__status__ = {k: [] for k in FS_STATUS.keys()}

    @lru_cache(maxsize=None)
    def _filtered(self, pootle_path, fs_path):
        return (
            (self.pootle_path
             and not fnmatch(pootle_path, self.pootle_path))
            or
            (self.fs_path
             and not fnmatch(fs_path, self.fs_path)))

    def _filtered_qs(self, qs):
        for store_fs in qs.iterator():
            if not self._filtered(store_fs.pootle_path, store_fs.path):
                yield store_fs

    @lru_cache(maxsize=None)
    def _get_changes(self, store_fs):
        fs_file = store_fs.file
        return fs_file.pootle_changed, fs_file.fs_changed
