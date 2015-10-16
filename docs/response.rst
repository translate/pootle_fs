Pootle FS responses
-------------------

Possible responses

``pulled_to_pootle``
  Stores updated where filesystem version was new or newer

``added_from_pootle``
  Files staged from Pootle that were new or newer than their files

``removed``
  Files/Stores that were staged for removal have been removed

``fetched_from_fs``
  Files staged from the filesystem that were new or newer than their Pootle
  Stores

``pushed_to_fs``
  Files updated where Pootle Store version was new or newer

``staged_for_merge_pootle``
  Files that have been staged for merging. In the event of conflicts in
  unit updates, Pootle wins

``staged_for_merge_fs``
  Files that have been staged for merging. In the event of conflicts in
  unit updates, FS wins

``merged_from_fs``
  File/Store were merged. Where there were conflicts in unit updates, FS won.

``merged_from_pootle``
  File/Store were merged. Where there were conflicts in unit updates, Pootle won.
