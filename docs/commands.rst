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


``config`` subcommand
---------------------

Print out the project FS configuration

.. code-block:: bash

   pootle fs myproject config

:option:`--update -u`
  Update the configuration from the FS .pootle.ini file


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
``sync_translations``.

:option:`--force`
  Stage files from FS that are conflicting


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


``rm_translations`` subcommand
-------------------------------

Stage for removal any matched Stores/files that do not have a corresponding
Store/file in Pootle/FS.

.. code-block:: bash

   pootle fs myproject rm_translations


``sync_translations`` subcommand
--------------------------------

Synchronize translations between FS and Pootle:

- Create stores in Pootle where they dont exist already
- Update exisiting stores from FS translation file
- Create files where not present
- Update existing files where Stores have changed
- Remove files/Stores staged for removal

.. code-block:: bash

   pootle fs myproject sync_translations


Path options
------------

:option:`--pootle_path -P`
  Only show/affect files where the pootle_path matches a given file glob.

:option:`--path -p`
  Only show/affect files where the FS path matches a given file glob.
