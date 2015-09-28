#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from .project_fs import _register_plugin


def _require_tp(language, project):
    """Helper to get/create a new translation project."""
    from pootle_translationproject.models import create_translation_project

    return create_translation_project(language, project)


@pytest.fixture
def english_tutorial(english, tutorial):
    """Require English Tutorial."""
    return _require_tp(english, tutorial)


@pytest.fixture
def english_tutorial_fs(english, tutorial):
    """Require English Tutorial."""
    _register_plugin()
    from pootle_fs.models import ProjectFS
    ProjectFS.objects.create(
        project=tutorial, fs_type="example")
    return _require_tp(english, tutorial)
