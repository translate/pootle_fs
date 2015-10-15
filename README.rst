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

The workflow for bringing translations from FS into Pootle is:

.. code-block::
   
   fetch_translations  >>>  pull_translations

Where ``fetch_translations`` will mark the importable translations, and
``pull_translations`` will actually sync the database.


The workflow for sending translations from Pootle to the FS:

.. code-block::
   
   add_translations  >>>  push_translations

Where ``add_translations`` will mark the exportable translations, and
``push_translations`` will actually sync the FS.


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
