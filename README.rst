Pootle FS
---------

Pootle FS app

An FS can be either a local filesystem or a VCS system such as git, svn, hg or
cvs.

The app uses a configuration syntax to create associations between Pootle
``Stores`` and file stores. The stores can then be synced and changes in either
can be tracked.


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


``fetch_translations`` subcommand
---------------------------------

Pull the FS repository if required, and on reading the ``.pootle.ini``
configuration file, create `FSStore` objects to track the associations.

.. code-block:: bash

   pootle fs myproject fetch_translations


``status`` subcommand
---------------------

List the status of files in Pootle and FS - specifically files that are:

- only in Pootle
- only in FS
- updated in Pootle
- updated in FS
- updated in both Pootle and FS

.. code-block:: bash

   pootle fs myproject status


``pull_translations`` subcommand
--------------------------------

Pull translations from FS into Pootle:

- Create stores in Pootle where they dont exist already
- Update exisiting stores from FS translation file

.. code-block:: bash

   pootle fs myproject pull_translations

(Proposed: add ``file_path`` argument to filter which translations to pull.)


---------------------------------------------

Proposed/unimplemented
^^^^^^^^^^^^^^^^^^^^^^


``add_translations`` subcommand
------------------------------

Add translations from Pootle into FS, using an optional ``pootle_path``
argument to filter which translations to add.


``push_translations`` subcommand
----------------------------------

Commit and push translations from Pootle into FS



