Pootle FS status
----------------

Possible status

``conflict``
  Both the pootle revision has changed since last sync and the latest_hash of
  the file has changed. The next step would be to ``fetch_translations``
  or ``add_translations`` using ``--force`` to keep the FS version or Pootle
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
  A new ``Store`` has been created in Pootle and has been staged using
  ``add_translations``. It has not yet been synced and does not exist in the FS.
  The next step would be to ``sync_translations`` to sync this ``Store``

``pootle_changed``
  A ``Store`` has changed in Pootle since the last sync. The next step would be
  to use ``sync_translations`` to push these changes to the FS.

``pootle_removed``
  A previously synced ``Store`` has been removed. The next step is would be to
  either use ``fetch_translations --force`` to restore the FS version, or to use
  ``rm_translations`` to stage for removal from FS.

``fs_untracked``
  A new file has been added in FS and matches a ``translation_path`` in
  ``.pootle.ini``, but does not have any ``StoreFS`` sync configuration. The
  next step would be to use ``fetch_translations`` to add a configuration.
  Alternatively, you can use ``rm_translations`` to stage for removal from FS.

``fs_added``
  A new file has been created in FS and has been staged using
  ``fetch_translations``. It has not yet been synced. The next step would be to
  ``sync_translations`` to create and sync this ``Store``

``fs_changed``
  A file has changed in FS since the last sync. The next step would be
  to use ``sync_translations`` to push these changes to the FS.

``fs_removed``
  A previously synced file has been removed from the FS. The next step is would be to
  either use ``add_translations --force`` to restore the Pootle version, or to use
  ``rm_translations`` to stage for removal from Pootle.


``to_remove``
  A file or Store that does not have a corresponding Store/file that has been
  staged for removal.


------
Not implemented
^^^^^^^^^^^^^^^

``both_removed``
  A previously synced file has been removed from the FS and Pootle - effectively
  orphaned. We may be able to use some kind of garbage collection to prevent this
  happening.
