.. _workflow:

Pootle FS Configuration
-----------------------

Configuring your project
========================

To set an FS plugin for a project, use the ``set_fs`` command:

.. code-block:: bash

   pootle fs $projectname set_fs $fs_type $fs_url

The ``$projectname`` must the name of a valid project in Pootle.

The ``fs_type`` should be an installed and registered FS plugin type - such
as ``git`` or ``local``.

The ``fs_url`` must be a URL specific to the type of FS plugin you are using.


Default configuration options in .ini file
==========================================

.. code-block:: ini

   [default]
   translation_path = /<lang>/<directory_path>/<filename>.po


Defining a translation_path
===========================


Defining a directory path
=========================
