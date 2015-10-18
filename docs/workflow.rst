.. _workflow:

Pootle filesystem Workflow
--------------------------


Syncing previously synced Stores/files
======================================

When a ``Store`` and corresponding file have been synced previously, they are
automatically staged for syncing if either changes.

This is not the case however if both have changed - see resolving conflicts
section for further information.

To re-sync ``Stores`` and files:

.. code-block:: bash

   (env) $ pootle fs myproject sync_translations


Pulling new translation files from the filesystem to Pootle
===========================================================

The workflow for bringing new translations from the filesystem into Pootle is:

.. code-block:: bash
   
   (env) $ pootle fs myproject fetch_translations
   (env) $ pootle fs myproject sync_translations

Where ``fetch_translations`` will stage the new translations, and
``sync_translations`` will actually sync to the database.

.. note:: You can fetch/sync specific ``Stores`` or files, or groups of them
	  using the ``-P`` and ``-p`` options to fetch_translations and
	  sync_translations.


Pushing new translation files from Pootle to the filesystem
===========================================================

The workflow for sending translations from Pootle to the filesystem:

.. code-block:: bash
   
   (env) $ pootle fs myproject add_translations
   (env) $ pootle fs myproject sync_translations

Where ``add_translations`` will stage the new translations, and
``sync_translations`` will actually sync to the filesystem.

.. note:: You can add/sync specific ``Stores`` or files, or groups of them
	  using the ``-P`` and ``-p`` options to add_translations and
	  sync_translations.


Resolving conflicts
===================

Conflicts can occur if both a Pootle ``Store`` and the corresponding file have
changed.

Conflict can also arise if a new Pootle ``Store`` is added and a matched file
has been added in the filesystem.


Resolving conflicts - overwriting Pootle with filesystem version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you wish to keep the version that is currently on the filesystem,
discarding all changes in Pootle, you can do the following:

.. code-block:: bash
   
   (env) $ pootle fs myproject fetch_translations --force
   (env) $ pootle fs myproject sync_translations



Resolving conflicts - overwriting filesystem with Pootle version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you wish to keep the version that is currently in Pootle,
discarding all changes in the filesystem, you can do the following:

.. code-block:: bash
   
   (env) $ pootle fs myproject add_translations --force
   (env) $ pootle fs myproject sync_translations


Resolving conflicts - merging
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to merge the changes made in both Pootle and the filesystem, you can:

.. code-block:: bash
   
   (env) $ pootle fs myproject merge_translations
   (env) $ pootle fs myproject sync_translations

When merging if there are conflicts in translation units the default behaviour
is to keep the filesystem version, and make the Pootle version into a suggestion.

You can reverse this behaviour as follows:

.. code-block:: bash
   
   (env) $ pootle fs myproject merge_translations --pootle-wins
   (env) $ pootle fs myproject sync_translations


Removing files/Stores
^^^^^^^^^^^^^^^^^^^^^

Sometimes a ``Store`` or file is unmatched on the other side, either because it
is newly added or because a ``Store`` or file has been removed.

You can remove ``Stores`` or files that do not have a corresponding match:

.. code-block:: bash
   
   (env) $ pootle fs myproject rm_translations
   (env) $ pootle fs myproject sync_translations

This will not affect any other ``Stores`` or files.
