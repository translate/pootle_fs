#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..fixtures.pootle_fs_fixtures.utils import (
    _register_plugin, _clear_plugins)


@pytest.mark.django_db
def test_add_project_fs(tutorial):
    from pootle_fs.models import ProjectFS
    _register_plugin()
    project_fs = ProjectFS.objects.create(
        project=tutorial, fs_type="example")
    project_fs.save()
    assert project_fs.pootle_config == ".pootle.ini"


@pytest.mark.django_db
def test_add_project_fs_again(tutorial):
    from pootle_fs.models import ProjectFS
    _register_plugin()
    project_fs = ProjectFS.objects.create(
        project=tutorial, fs_type="example")
    project_fs.save()

    with pytest.raises(IntegrityError):
        project_fs = ProjectFS.objects.create(
            project=tutorial, fs_type="example")
        project_fs.save()


@pytest.mark.django_db
def test_add_project_fs_no_plugins(tutorial):
    from pootle_fs.models import ProjectFS
    _clear_plugins()

    with pytest.raises(ValidationError):
        ProjectFS.objects.create(
            project=tutorial, fs_type="example")


@pytest.mark.django_db
def test_add_project_fs_no_project(tutorial):
    from pootle_fs.models import ProjectFS
    _register_plugin()

    with pytest.raises(IntegrityError):
        ProjectFS.objects.create(fs_type="example")


@pytest.mark.django_db
def test_add_project_fs_no_fs_type(tutorial):
    from pootle_fs.models import ProjectFS
    _register_plugin()

    with pytest.raises(ValidationError):
        ProjectFS.objects.create(project=tutorial)


@pytest.mark.django_db
def test_add_project_fs_bad_fs_type(tutorial):
    from pootle_fs.models import ProjectFS
    _register_plugin()

    with pytest.raises(ValidationError):
        ProjectFS.objects.create(
            project=tutorial, fs_type="BAD")


@pytest.mark.django_db
def test_save_project_fs_type(tutorial_fs):
    _register_plugin(name="other", clear=False)
    tutorial_fs.fs_type = "other"
    tutorial_fs.save()
    assert tutorial_fs.fs_type == "other"


@pytest.mark.django_db
def test_save_project_bad_fs_type(tutorial_fs):
    tutorial_fs.fs_type = "BAD"

    with pytest.raises(ValidationError):
        tutorial_fs.save()


@pytest.mark.django_db
def test_save_project_fs_type_gone(tutorial_fs):
    """If the plugin that was registered is no longer available
    you cannot save the project_fs unless you swithc to valid
    plugin
    """

    _clear_plugins()
    _register_plugin(name="other")

    with pytest.raises(ValidationError):
        tutorial_fs.save()

    tutorial_fs.fs_type = "other"
    tutorial_fs.save()
