#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from ..fixtures.pootle_fs_fixtures import _clear_plugins
from pootle_fs import Plugin, plugins


@pytest.mark.django
def test_register_plugin():
    _clear_plugins()

    class ExamplePlugin(Plugin):
        name = "example"

    plugins.register(ExamplePlugin)

    assert "example" in plugins
    assert plugins["example"] == ExamplePlugin
