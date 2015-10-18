Pootle FS
---------

Pootle FS app provides a plugin framework for synchronizing external
filesystems containing localisation files.


.. image:: https://img.shields.io/travis/translate/pootle_fs.svg?style=flat-square
    :alt: Build Status
    :target: https://travis-ci.org/translate/pootle_fs

An FS can be either a local filesystem or a VCS system such as git, svn, hg or
cvs.

The app uses a configuration syntax to create associations between Pootle
``Stores`` and file stores. The stores can then be synced and changes in either
can be tracked.

Syncing is a 2-step process in which changes to Stores/files are initially
staged with any or all of:

- ``add_translations``
- ``fetch_translations``
- ``rm_translations``
- ``merge_translations``

Changes to previously synced Stores/files are automatically staged for
synchronisation, where no conflict exists.

Once the desired changes have been staged ``sync_translations`` is called to
perform the synchronisation.


Installation
============

``pootle_fs`` does not provide any specific plugins so need to install
a backend plugin also.

Currently the only implemented plugin is for `Git <./docs/plugins/git.rst>`_

Neither ``pootle_fs`` nor ``pootle_fs_git`` are on Pypi so only dev install
is possible.

Also requires the ``no_mtime`` branch of pootle:

`<https://github.com/phlax/pootle/tree/no_mtime>`_


Further reading
===============

- `Workflow <docs/workflow.rst>`_
- `Configuration <docs/configuration.rst>`_
- `Status <docs/status.rst>`_
- `Commands <docs/commands.rst>`_
- `Response <docs/response.rst>`_
- `Git plugin <docs/plugins/git.rst>`_


Related software
================

- `pootle_fs_git <https://github.com/translate/pootle_fs_git>`_
- `pootle_fs_scheduler <https://github.com/phlax/pootle_fs_scheduler>`_
- `pootle_fs_web <https://github.com/phlax/pootle_fs_web>`_
