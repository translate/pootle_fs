Pootle FS
---------

Pootle FS app

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

This command is the functional opposite of the ``add_translations`` command.

If you use the ``--force`` option it will add new translations associations
from the FS that are already present in the Pootle.

This command does not add any translation files in the FS - for that you need to
``pull_translations``.


``pull_translations`` subcommand
--------------------------------

Pull translations from FS into Pootle:

- Create stores in Pootle where they dont exist already
- Update exisiting stores from FS translation file

.. code-block:: bash

   pootle fs myproject pull_translations

(Proposed: add ``file_path`` argument to filter which translations to pull.)



``add_translations`` subcommand
------------------------------

Add translations from Pootle into FS, using an optional ``pootle_path``
argument to filter which translations to add.

This command is the functional opposite of the ``fetch_translations`` command.

If you use the ``--force`` option it will add new translations from Pootle that
are already present in the FS.

This command does not add any translation files in the FS - for tht you need to
``push_translations``.


``push_translations`` subcommand
----------------------------------

Commit and push translations from Pootle into FS




``status`` subcommand
---------------------

List the status of files in Pootle and FS

.. code-block:: bash

   pootle fs myproject status

Possible status

``conflict``
  Both the pootle revision has changed since last sync and the latest_hash of
  the file has changed. The next step would be to either ``pull_translations``
  or ``push_translations`` using ``--force`` to keep the FS version or Pootle
  version respectively.

``conflict_untracked``
  A conflict can also arise if a file on the FS has status ``fs_untracked`` and a
  matching ``Store`` has status ``pootle_untracked`` in this case you can use either
  ``fetch_translations`` or ``add_translations`` with ``--force`` depending on
  whether you want to keep the FS file or the ``Store``.

``pootle_untracked``
  A new store has been added in Pootle and matches a ``translation_path`` in
  ``.pootle.ini``, but does not have any ``StoreFS`` sync configuration. The
  next step would be to use ``add_translations`` to add a configuration.

``pootle_added``
  A new ``Store`` has been added in Pootle and has been added using
  ``add_translations``. It has not yet been synced and does not exist in the FS.
  The next step would be to ``push_translations`` to sync this ``Store``

``pootle_changed``
  A ``Store`` has changed in Pootle since the last sync. The next step would be
  to use ``push_translations`` to push these changes to the FS.

``pootle_removed``
  A previously synced ``Store`` has been removed.

``fs_untracked``
  A new file has been added in FS and matches a ``translation_path`` in
  ``.pootle.ini``, but does not have any ``StoreFS`` sync configuration. The
  next step would be to use ``fetch_translations`` to add a configuration.

``fs_added``
  A new file has been added in FS and has been added using
  ``fetch_translations``. It has not yet been synced. The next step would be to
  ``pull_translations`` to create and sync this ``Store``

``fs_changed``
  A file has changed in FS since the last sync. The next step would be
  to use ``push_translations`` to push these changes to the FS.

``fs_removed``
  A previously synced file has been removed from the FS

``both_removed``
  A previously synced file has been removed from the FS and Pootle - effectively
  orphaned. We may be able to use some kind of garbage collection to prevent this
  happening.

