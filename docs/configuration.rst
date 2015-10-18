.. _workflow:

Pootle FS Configuration
-----------------------

Configuring your project in Pootle
==================================

To set an FS plugin for a project, use the ``set_fs`` command:

.. code-block:: bash

   pootle fs MYPROJECT set_fs FS_TYPE FS_URL

``MYPROJECT`` must the name of a valid project in Pootle.

``FS_TYPE`` should be an installed and registered FS plugin type - such
as ``git`` or ``local``.

``FS_URL`` must be a URL specific to the type of FS plugin you are using.


Creating a .pootle.ini on your filesystem
=========================================

When pootle_fs first pulls your filesystem it looks for a file ``.pootle.ini``
to set up the configuration of your project.

The configuration file uses the ``ini`` syntax.

You can see the current configuration for your project as follows:

.. code-block:: bash

   pootle fs MYPROJECT config


Updating the configuration
==========================

If you make changes to your ``.pootle.ini`` file they do not take affect until
you have updated the configuration:

.. code-block:: bash

   pootle fs MYPROJECT config --update



Defining a translation_path
===========================




Defining a directory path
=========================

