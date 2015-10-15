Pootle FS commands
------------------

Pootle FS commands


``fs`` command
--------------

Get FS info for all projects

.. code-block:: bash

   pootle fs


``set_fs`` subcommand
---------------------

Set the FS for a project. Project must exist in Pootle.

.. code-block:: bash

   pootle fs myproject set_fs git git@github.com:translate/myprojrepo


``info`` subcommand
-------------------

Get the FS info for a project. This is the default command - so ``info`` can
be ommitted.

.. code-block:: bash

   pootle fs myproject info

or...

.. code-block:: bash

   pootle fs myproject


``status`` subcommand
---------------------

List the status of files in Pootle and FS

.. code-block:: bash

   pootle fs myproject status


``fetch_translations`` subcommand
---------------------------------

Pull the FS repository if required, and on reading the ``.pootle.ini``
configuration file, create `FSStore` objects to track the associations.

.. code-block:: bash

   pootle fs myproject fetch_translations

This command is the functional opposite of the ``add_translations`` command.

This command does not add any translation files in the FS - for that you need to
``pull_translations``.

:option:`--force`
  Stage files from FS that are conflicting


``pull_translations`` subcommand
--------------------------------

Pull translations from FS into Pootle:

- Create stores in Pootle where they dont exist already
- Update exisiting stores from FS translation file

.. code-block:: bash

   pootle fs myproject pull_translations

:option:`--prune`
  Remove files from Pootle that are not present in FS


``add_translations`` subcommand
-------------------------------

Add translations from Pootle into FS, using an optional ``pootle_path``
argument to filter which translations to add.

This command is the functional opposite of the ``fetch_translations`` command.

If you use the ``--force`` option it will add new translations from Pootle that
are already present in the FS.

This command does not add any translation files in the FS - for tht you need to
``push_translations``.

:option:`--force`
  Stage files from Pootle that are conflicting


``push_translations`` subcommand
--------------------------------

Commit and push translations from Pootle into FS

:option:`--prune`
  Remove files from Pootle that are not present in FS


Path options
------------

:option:`--pootle_path`
  Only show/affect files where the pootle_path matches a given file glob.

:option:`--path`
  Only show/affect files where the FS path matches a given file glob.
