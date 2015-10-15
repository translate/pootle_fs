Pootle FS status
----------------

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

