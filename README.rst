Pootle FS
---------

Pootle FS app

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

Changes to previously synced Stores/files are automatically staged for
synchronisation, where no conflict exists.

Once the desired changes have been staged ``sync_translations`` is called to
perform the synchronisation.

The workflow for bringing translations from FS into Pootle is:

.. code-block::
   
   fetch_translations  >>>  sync_translations

Where ``fetch_translations`` will stage the importable translations, and
``sync_translations`` will actually sync to the database.


The workflow for sending translations from Pootle to the FS:

.. code-block::
   
   add_translations  >>>  sync_translations

Where ``add_translations`` will stage the exportable translations, and
``sync_translations`` will actually sync to the FS.


Further reading
===============

- `Workflow <docs/workflow.rst>`_
- `Configuration <docs/configuration.rst>`_
- `Status <docs/status.rst>`_
- `Commands <docs/commands.rst>`_
- `Response <docs/response.rst>`_


Related software
================

- `pootle_fs_git <https://github.com/translate/pootle_fs_git>`_
- `pootle_fs_scheduler <https://github.com/phlax/pootle_fs_scheduler>`_
- `pootle_fs_web <https://github.com/phlax/pootle_fs_web>`_
