from datetime import datetime
from md5 import md5
import os
import shutil


EXAMPLE_FS = os.path.join(os.path.dirname(__file__), "data/fs/example_fs")

STATUS_TYPES = [
    "pootle_ahead", "pootle_added", "pootle_untracked", "pootle_removed",
    "fs_ahead", "fs_added", "fs_untracked", "fs_removed",
    "conflict", "conflict_untracked"]


def _require_language(code, fullname, plurals=2, plural_equation='(n != 1)'):
    """Helper to get/create a new language."""
    from pootle_language.models import Language

    criteria = {
        'code': code,
        'fullname': fullname,
        'nplurals': plurals,
        'pluralequation': plural_equation,
    }
    language, created = Language.objects.get_or_create(**criteria)

    return language


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


def _require_tp(language, project):
    """Helper to get/create a new translation project."""
    from pootle_translationproject.models import create_translation_project

    return create_translation_project(language, project)


def _require_store(tp, po_dir, name):
    """Helper to get/create a new store."""
    from pootle_store.models import Store

    file_path = os.path.join(po_dir, tp.real_path, name)
    parent_dir = tp.directory
    pootle_path = tp.pootle_path + name

    try:
        store = Store.objects.get(
            pootle_path=pootle_path,
            translation_project=tp,
        )
    except Store.DoesNotExist:
        store = Store.objects.create(
            file=file_path,
            parent=parent_dir,
            name=name,
            translation_project=tp,
        )

    return store


def _require_user(username, fullname, password=None, is_superuser=False):
    """Helper to get/create a new user."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    criteria = {
        'username': username,
        'full_name': fullname,
        'is_active': True,
        'is_superuser': is_superuser,
    }
    user, created = User.objects.get_or_create(**criteria)
    if created:
        if password is None:
            user.set_unusable_password()
        else:
            user.set_password(password)
        user.save()

    return user


def _register_plugin(name="example", plugin=None, clear=True, src=EXAMPLE_FS):
    if clear:
        _clear_plugins()

    from pootle_fs import Plugin, plugins, FSFile

    class ExampleFSFile(FSFile):

        @property
        def latest_hash(self):
            if self.exists:
                return md5(str(os.stat(self.file_path).st_mtime)).hexdigest()

    class ExamplePlugin(Plugin):

        file_class = ExampleFSFile
        _pulled = False

        def get_latest_hash(self):
            return md5(str(datetime.now())).hexdigest()

        def pull(self):
            dir_path = self.local_fs_path
            if not self._pulled:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                shutil.copytree(
                    os.path.abspath(
                        os.path.join(
                            __file__,
                            self.src)),
                    os.path.abspath(dir_path))
            self._pulled = True

    ExamplePlugin.name = name
    ExamplePlugin.src = os.path.abspath(src)
    plugins.register(plugin or ExamplePlugin)
    return ExamplePlugin


def _clear_plugins():
    from pootle_fs import plugins
    plugins.__plugins__ = {}


def _fake_pull(dir_path, src=EXAMPLE_FS):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    shutil.copytree(
        os.path.abspath(
            os.path.join(
                __file__,
                src)),
        os.path.abspath(dir_path))


po_config = """
[default]
translation_path = po/<lang>.po
"""


def _create_conflict(plugin):
    _setup_store(
        plugin,
        path="subdir3/subsubdir/example5.po")
    _edit_file(
        plugin,
        "non_gnu_style/locales/en/subsubdir/example5.po")


def _test_status(plugin, expected):
    status = plugin.status()
    assert status.has_changed is (expected and True or False)
    for k in STATUS_TYPES:
        if k in expected:
            assert expected[k] == [
                (s.pootle_path, s.fs_path)
                for s in status[k]]
            assert k in status
        else:
            assert status[k] == []
            assert k not in status


def _edit_file(plugin, filepath):
    po_file = (os.path.join(plugin.local_fs_path, filepath))
    dir_name = os.path.dirname(po_file)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    with open(po_file, "w") as f:
        f.write(str(datetime.now()))


def _remove_file(plugin, path):
    # remove the file from FS
    os.unlink(os.path.join(plugin.local_fs_path, path))


def _update_store(plugin=None, pootle_path=None):
    from pootle_store.models import Unit, Store
    if pootle_path:
        store = Store.objects.get(pootle_path=pootle_path)
    else:
        # Update the store revision
        store = plugin.stores.first()
    unit = Unit.objects.create(
        unitid="Foo",
        source="Foo",
        store=store,
        index=0,
        revision=store.get_max_unit_revision() or 1)
    unit.target = "Bar"
    unit.save()


def _remove_store(plugin=None, pootle_path=None):
    from pootle_store.models import Store
    if pootle_path:
        store = Store.objects.get(pootle_path=pootle_path)
    else:
        # Update the store revision
        store = plugin.stores.first()
    # Remove the store
    store.delete()


def _setup_dir(dir_path, makepo=True):
    src = os.path.join(dir_path, "src")
    if os.path.exists(src):
        shutil.rmtree(src)
    po_path = os.path.join(src, "po")
    os.makedirs(po_path)
    if makepo:
        with open(os.path.join(po_path, "en.po"), "w") as f:
            f.write(" ")
    with open(os.path.join(src, ".pootle.ini"), "w") as f:
        f.write(po_config)
    return src


def _setup_store(tutorial_fs, path="en.po"):
    from pootle_store.models import Store
    tp = tutorial_fs.project.translationproject_set.get(
        language__code="en")
    parts = path.strip("/").split("/")
    directory = tp.directory
    for part in parts[:-1]:
        directory = directory.child_dirs.get(name=part)
    store = Store.objects.create(
        translation_project=tp, parent=directory, name=parts[-1])
    return store


def _clear_fs(dir_path, tutorial_fs):
    tutorial_path = os.path.join(dir_path, tutorial_fs.project.code)
    if os.path.exists(tutorial_path):
        shutil.rmtree(tutorial_path)
