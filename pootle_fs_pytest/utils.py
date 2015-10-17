from datetime import datetime
import logging
from md5 import md5
import os
import shutil
import uuid

from translate.storage.po import pounit


logger = logging.getLogger(__name__)

EXAMPLE_FS = os.path.join(os.path.dirname(__file__), "data/fs/example_fs")

STATUS_TYPES = [
    "pootle_ahead", "pootle_added", "pootle_untracked", "pootle_removed",
    "fs_ahead", "fs_added", "fs_untracked", "fs_removed",
    "conflict", "conflict_untracked"]

PO_CONFIG = """
[default]
translation_path = po/<lang>.po
"""

PO_FILE = """
# Comment
msgid ""
msgstr ""
"Project-Id-Version: Translate tutorial 1.0\\n"
"Report-Msgid-Bugs-To: translate-devel@lists.sourceforge.net\\n"
"POT-Creation-Date: 2008-11-25 10:03+0200\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"Language: en\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"X-Generator: Translate Toolkit 1.2.0\\n"


#. Hello, world
msgid "Hello, world %s"
msgstr "Hello, world %s"

"""

PO_UPDATE = """

#. PO Update %s
msgid "PO Update %s"
msgstr "PO updated %s"
"""

TEST_SUITE_STATUS = [
    'conflict', 'conflict_untracked',
    'pootle_ahead', 'pootle_untracked', 'pootle_removed',
    'fs_ahead', 'fs_untracked']


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


def _register_plugin(name="example", plugin=None, clear=True):
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

        def push(self, response):
            if os.path.exists(self.fs.url):
                shutil.rmtree(self.fs.url)
            shutil.copytree(
                self.local_fs_path,
                self.fs.url)
            return response

        def pull(self):
            if os.path.exists(self.local_fs_path):
                shutil.rmtree(self.local_fs_path)
            shutil.copytree(
                self.fs.url,
                self.local_fs_path)

    ExamplePlugin.name = name
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


def _create_conflict(plugin, path=None, edit_file=None):
    _ef = edit_file or _edit_file
    from pootle_fs.models import StoreFS
    if path is not None:
        store_fs = StoreFS.objects.get(
            pootle_path=path)
        pootle_path = store_fs.pootle_path
        fs_path = store_fs.path
        _update_store(plugin, pootle_path)
    else:
        pootle_path = "/en/tutorial/subdir3/subsubdir/example5.po"
        fs_path = "/non_gnu_style/locales/en/subsubdir/example5.po"
        _setup_store(pootle_path)
    _ef(
        plugin,
        fs_path)


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
    po_file = (os.path.join(plugin.fs.url, filepath.strip("/")))
    dir_name = os.path.dirname(po_file)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    with open(po_file, "ar+") as f:
        f.seek(0)
        existing = f.read()
        if not existing:
            uid = uuid.uuid4().hex
            content = PO_FILE % (uid, uid)
        else:
            update_id = str(datetime.now())
            content = (
                PO_UPDATE
                % (update_id, update_id, update_id))
        f.write(content)


def _remove_file(plugin, path):
    # remove the file from FS
    os.unlink(os.path.join(plugin.fs.url, path.strip("/")))


def _update_store(plugin, pootle_path):
    from django.contrib.auth import get_user_model

    from pootle_store.models import Store, Revision

    store = Store.objects.get(pootle_path=pootle_path)
    revision = Revision.incr()
    uid = uuid.uuid4().hex
    unitid = "New unit %s" % uid
    unit = pounit(unitid)
    unit.target = "Bar %s" % uid
    user = plugin.pootle_user
    if user is None:
        User = get_user_model()
        user = User.objects.get_system_user()
    unit.store = store
    unit = store.addunit(unit, user=user, revision=revision)
    store.save()


def _remove_store(pootle_path):
    from pootle_store.models import Store
    store = Store.objects.get(pootle_path=pootle_path)
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
        f.write(PO_CONFIG)
    return src


def _setup_store(pootle_path):
    from pootle_store.models import Store
    from pootle_translationproject.models import TranslationProject

    parts = pootle_path.strip("/").split("/")
    tp = TranslationProject.objects.get(
        language__code=parts[0], project__code=parts[1])
    directory = tp.directory
    for part in parts[2:-1]:
        directory = directory.child_dirs.get(name=part)
    store = Store.objects.create(
        translation_project=tp, parent=directory, name=parts[-1])
    return store


def _clear_fs(dir_path, tutorial_fs):
    tutorial_path = os.path.join(dir_path, tutorial_fs.project.code)
    if os.path.exists(tutorial_path):
        shutil.rmtree(tutorial_path)


def _setup_export_dir(dir_path, settings):
    export_dir = os.path.join(dir_path, "__exports__")
    if os.path.exists(export_dir):
        shutil.rmtree(export_dir)
    settings.CACHES['exports']['LOCATION'] = export_dir


def create_test_suite(plugin, edit_file=None, remove_file=None):
    plugin.fetch_translations()
    plugin.sync_translations()
    _ef = edit_file or _edit_file
    _ef(plugin, "non_gnu_style/locales/en/foo/bar/baz.po")
    _ef(plugin, "gnu_style_named_folders/po-example10/en.po")
    _ef(plugin, "gnu_style/po/zu.po")
    _rf = remove_file or _remove_file
    _rf(plugin, "gnu_style/po/en.po")
    _create_conflict(
        plugin,
        edit_file=edit_file)
    _create_conflict(
        plugin, "/zu/tutorial/subdir3/subsubdir/example4.po",
        edit_file=edit_file)
    _update_store(plugin, "/en/tutorial/subdir2/example2.po")
    _setup_store("/en/tutorial/subdir2/example11.po")
    _remove_store("/en/tutorial/subdir2/example1.po")
    status = plugin.status()

    for k in TEST_SUITE_STATUS:
        assert k in status
    return plugin


def create_plugin(fs_type, fs_plugin, register=True):
    from pootle_fs.models import ProjectFS
    if register:
        _register_plugin(fs_type)
    kwargs = dict(
        project=fs_plugin[0],
        fs_type=fs_type,
        url=fs_plugin[2])
    return ProjectFS.objects.create(**kwargs).plugin
