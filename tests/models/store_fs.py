#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_fs.models import StoreFS, ProjectFS

from django.core.exceptions import ValidationError
from django.db import IntegrityError


@pytest.mark.django_db
def test_add_new_store_fs(tutorial_fs):
    """Add a store_fs for a store that doesnt exist yet
    """
    pootle_path = "/en/tutorial/example.po"
    fs_path = "/some/fs/example.po"
    store_fs = StoreFS.objects.create(
        pootle_path=pootle_path,
        path=fs_path)
    assert store_fs.project == tutorial_fs.project
    assert store_fs.store is None
    assert store_fs.pootle_path == pootle_path
    assert store_fs.path == fs_path
    assert store_fs.last_sync_hash is None
    assert store_fs.last_sync_mtime is None
    assert store_fs.last_sync_revision is None


@pytest.mark.django_db
def test_add_store_fs_by_path(en_tutorial_po):
    """Add a store_fs for pootle_path
    """
    fs_path = "/some/fs/example.po"
    pootle_path = en_tutorial_po.pootle_path
    project = en_tutorial_po.translation_project.project
    ProjectFS.objects.create(
        project=project,
        fs_type="example")
    store_fs = StoreFS.objects.create(
        pootle_path=pootle_path,
        path=fs_path)
    assert store_fs.project == project
    assert store_fs.store == en_tutorial_po
    assert store_fs.pootle_path == pootle_path
    assert store_fs.path == fs_path
    assert store_fs.last_sync_hash is None
    assert store_fs.last_sync_mtime is None
    assert store_fs.last_sync_revision is None


@pytest.mark.django_db
def test_add_store_fs_by_store(en_tutorial_po):
    """Add a store_fs using store= rather than pootle_path
    """
    fs_path = "/some/fs/example.po"
    project = en_tutorial_po.translation_project.project
    ProjectFS.objects.create(
        project=project,
        fs_type="example")
    store_fs = StoreFS.objects.create(
        store=en_tutorial_po,
        path=fs_path)
    assert store_fs.project == project
    assert store_fs.store == en_tutorial_po
    assert store_fs.pootle_path == en_tutorial_po.pootle_path
    assert store_fs.path == fs_path
    assert store_fs.last_sync_hash is None
    assert store_fs.last_sync_mtime is None
    assert store_fs.last_sync_revision is None


@pytest.mark.django_db
def test_add_store_bad_project(tutorial_fs):
    """Try to create a store_fs by pootle_path for a non existent project
    """
    with pytest.raises(ValidationError):
        StoreFS.objects.create(
            pootle_path="/en/tutorial_BAD/example.po",
            path="/some/fs/example.po")


@pytest.mark.django_db
def test_add_store_bad_lang(tutorial_fs):
    """Try to create a store_fs by pootle_path for a non existent language
    """
    with pytest.raises(ValidationError):
        StoreFS.objects.create(
            pootle_path="/fr/tutorial/example.po",
            path="/some/fs/example.po")


@pytest.mark.django_db
def test_add_store_bad_path(en_tutorial_po):
    """Try to create a store_fs where pootle_path and store.pootle_path dont
     match.
    """
    fs_path = "/some/fs/example.po"
    ProjectFS.objects.create(
        project=en_tutorial_po.translation_project.project,
        fs_type="example")
    return
    with pytest.raises(ValidationError):
        try:
            StoreFS.objects.create(
                store=en_tutorial_po,
                pootle_path="/en/tutorial/example.po",
                path=fs_path)
        except IntegrityError:
            raise ValidationError


@pytest.mark.django_db
def test_save_store_fs_change_pootle_path_or_store(en_tutorial_po_fs_store):
    """You cant change a pootle_path if a store is associated
    unless you also remove the store association - and vice versa
    """
    fs_store = en_tutorial_po_fs_store
    store = fs_store.store
    other_path = "/en/tutorial/other.po"

    fs_store.pootle_path = other_path
    with pytest.raises(ValidationError):
        fs_store.save()
    fs_store.store = None
    fs_store.save()

    assert fs_store.store is None
    assert fs_store.pootle_path == other_path

    fs_store.store = store
    with pytest.raises(ValidationError):
        fs_store.save()

    fs_store.pootle_path = store.pootle_path
    fs_store.save()

    assert fs_store.store == store
    assert fs_store.pootle_path == store.pootle_path


@pytest.mark.django_db
def test_save_store_fs_bad_lang(en_tutorial_po_fs_store):
    fs_store = en_tutorial_po_fs_store
    fs_store.store = None
    fs_store.pootle_path = "/fr/tutorial/example.po"

    with pytest.raises(ValidationError):
        fs_store.save()


@pytest.mark.django_db
def test_save_store_fs_bad_path(en_tutorial_po_fs_store, en_tutorial_po):
    fs_store = en_tutorial_po_fs_store
    fs_store.store = en_tutorial_po
    fs_store.pootle_path = "/en/tutorial/example.po"
    return
    with pytest.raises(ValidationError):
        try:
            fs_store.save()
        except IntegrityError:
            raise ValidationError


@pytest.mark.django_db
def test_save_store_fs_bad_project(en_tutorial_po_fs_store):
    """Try to create a store_fs by pootle_path for a non existent project
    """
    fs_store = en_tutorial_po_fs_store
    fs_store.store = None
    fs_store.pootle_path = "/en/tutorial_BAD/example.po"
    with pytest.raises(ValidationError):
        fs_store.save()
