.. _pootle_fs_git:

Pootle FS Git plugin
--------------------

Installation
============

Currently only available for developer install:

`<https://github.com/translate/pootle_fs_git>`_


The core pootle_fs app is also required (also dev only):

`<https://github.com/translate/pootle_fs>`_


Currently also requires the ``no_mtime`` branch of pootle:

`<https://github.com/phlax/pootle/tree/no_mtime>`_


Pootle configuration
====================

.. code-block:: bash

   (env) $ pootle fs MYPROJECT set_fs git GIT_URL


``MYPROJECT`` should be the name of a project in your Pootle site.

``GIT_URL`` should be git ssh url.


Git authentication
==================

Currently only ssh authentication is supported.

The user running the pootle commands therefore must have a working ssh
environment and read/write access to the git repository in order to synchronize.


Custom .pootle.ini options
==========================

When using the git pootle_fs plugin there are some git-specific options

.. code-block:: bash

   [default]
   commit_message = "A custom commit message..."
   author_name = "My Self"
   author_email = "me@my.domain"
   committer_name = "Pootle Server"
   committer_email = "pootle@my.server"


Further reading
===============

- `Workflow <../workflow.rst>`_
- `Status <../status.rst>`_
- `Commands <../commands.rst>`_
