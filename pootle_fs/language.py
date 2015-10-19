# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle_language.models import Language


LANG_MAP_PRESETS = {
    "foo": (
        ("foo1", "en"),
        ("foo2", "foo20"),
        ("foo3", "foo30")),
    "bar": (
        ("bar1", "es"),
        ("bar2", "bar20"),
        ("bar3", "bar30")),
    "baz": (
        ("baz1", "zu"),
        ("baz2", "baz20"),
        ("baz3", "baz30"))}


logger = logging.getLogger(__name__)


class LanguageMapper(object):
    """For a given code find the relevant pootle lang taking account of any
    lang mapping configuration

    """

    def __init__(self, mapping, presets=None):
        self.mapping = mapping
        if presets is None:
            self.presets = LANG_MAP_PRESETS
        else:
            self.presets = presets

    def __getitem__(self, k):
        return self.get_lang(k)

    def __contains__(self, k):
        return k in self.lang_mappings

    @cached_property
    def lang_mappings(self):
        return self._parse_lang_mappings(self.mapping)

    def get_fs_code(self, pootle_code):
        for fs_code, pootle_code in self.lang_mappings.items():
            if pootle_code == pootle_code:
                return fs_code
        return pootle_code

    @lru_cache(maxsize=None)
    def get_lang(self, lang_code):
        try:
            return Language.objects.get(
                code=self.get_pootle_code(lang_code))
        except Language.DoesNotExist:
            return None

    def get_pootle_code(self, lang_code):
        return self.lang_mappings.get(lang_code, lang_code)

    def _parse_lang_mappings(self, mapping):
        _mapping = {}

        def _add_lang_mapping(k, v):
            # as its a 1-2-1 mapping remove any previous items with
            # same value
            if v in _mapping.values():
                for _k, _v in _mapping.items():
                    if v == _v:
                        del _mapping[_k]
                        break
            _mapping[k] = v

        for line in mapping:
            if line.strip().startswith("$"):
                preset = self.presets.get(line.strip()[1:], None)
                if not preset:
                    logger.warning(
                        "Unrecognised lang mapping preset: %s" % preset)
                else:
                    for k, v in preset:
                        _add_lang_mapping(k, v)
            else:
                try:
                    _add_lang_mapping(
                        *[x for x
                          in line.strip().split(" ")
                          if x.strip()])
                except (ValueError, TypeError):
                    logger.warning("Misconfigured lang mapping: %s" % line)
        return _mapping
