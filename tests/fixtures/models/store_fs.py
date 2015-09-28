#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


@pytest.fixture
def en_tutorial_po_fs_store(en_tutorial_fs_po):
    """Require the /en/tutorial/tutorial.po store."""
    from pootle_fs.models import StoreFS
    return StoreFS.objects.create(
        store=en_tutorial_fs_po,
        path="/some/fs/path")
