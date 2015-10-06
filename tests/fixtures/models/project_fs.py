#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from ..pootle_fs_fixtures.utils import _register_plugin


@pytest.fixture
def tutorial_fs(tutorial):
    from pootle_fs.models import ProjectFS
    return ProjectFS.objects.create(
        project=tutorial,
        fs_type="example",
        url=_register_plugin().src)
