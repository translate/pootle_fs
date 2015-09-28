#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


def _require_project(code, name, source_language, **kwargs):
    """Helper to get/create a new project."""
    from pootle_project.models import Project

    criteria = {
        'code': code,
        'fullname': name,
        'source_language': source_language,
        'checkstyle': 'standard',
        'localfiletype': 'po',
        'treestyle': 'auto',
    }
    criteria.update(kwargs)

    new_project, created = Project.objects.get_or_create(**criteria)
    return new_project


@pytest.fixture
def tutorial(projects, english):
    """Require `tutorial` test project."""
    return _require_project('tutorial', 'Tutorial', english)
