Pootle FS Documentation
=======================

Pootle FS app provides a plugin framework for synchronizing external
filesystems containing localisation files.

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
- ``merge_translations``

Changes to previously synced Stores/files are automatically staged for
synchronisation, where no conflict exists.

Once the desired changes have been staged ``sync_translations`` is called to
perform the synchronisation.

.. toctree::
   :maxdepth: 1

   configuration
   workflow
   commands
   status
   responses
   plugins/git
