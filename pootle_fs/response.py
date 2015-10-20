# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict
import logging

from pootle_store.models import Store

from .models import StoreFS
from .status import Status


logger = logging.getLogger(__name__)

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


class ActionStatus(Status):

    def __init__(self, action_type, original_status, complete=True, msg=None):
        self.action_type = action_type
        self.complete = complete
        self.original_status = original_status

    def __str__(self):
        if self.failed:
            failed = " FAILED"
        else:
            failed = ""
        return (
            "<FSAction(%s)%s: %s %s>"
            % (self.store_fs.project, failed,
               self.action_type, self.pootle_path))

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
    def plugin(self):
        return self.original_status.plugin

    @property
    def project(self):
        return self.original_status.project

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
