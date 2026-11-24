# CSW result pipeline — verified installed source snapshots

These two scripts are byte-identical snapshots of the production scripts under
`/Users/homeserver/.hermes/profiles/hermes-wrestling/scripts/` after the
WinnerString correction (task `t_05b54f87`). They are versioned here for review,
regression tests and recovery; the scheduler still invokes the installed copies.

For `RoyalRumble=true`, saved MotW slots are not an authoritative result roster:
extra participants are added by a separate mod before the match. WinnerString
is the real winner. LoserString such as `29 other wrestlers` contains no names,
so it creates neither named losses nor phantom participants/draws. Named losers
are retained. PWI counts a known winner even if losers are anonymous.

Normal matches retain structural member resolution: WinnerString/LoserString
can contain **team labels**, not individual wrestler names. A real-export
differential verified all 1,267 non-Rumble rows unchanged; all 32 Rumble rows
were corrected without modifying the XML.

Tests against versioned snapshots:

```
/usr/bin/python3 -m unittest discover -s tests -p test_csw_rumble_results.py -v
```

Tests against production installation:

```
CSW_RESULTS_SCRIPTS=/Users/homeserver/.hermes/profiles/hermes-wrestling/scripts \
  /usr/bin/python3 -m unittest discover -s tests -p test_csw_rumble_results.py -v
```

Export requires explicit `CHOKE_SLAM_XML`, `CHOKE_SLAM_REPO`,
`CHOKE_SLAM_EXCEL`, `CHOKE_SLAM_EDITS` and `CHOKE_SLAM_SKIP_PUSH=1`.
`part1_xml_to_excel` also updates the Nextcloud export; follow with a targeted
Nextcloud scan. Do not use importer execution as a read-only probe without
isolating that sharing side effect.

For this migration, `npm run sync:site -- --preserve-orphans` explicitly retains
historical profile notes that are no longer in the result-derived index.
The default mass-deletion guard remains unchanged. Only the two S08E04 phantom
profiles (Strong/Kobashi), their published pages and their charts were explicitly
removed. Other retained historical notes need a separate provenance decision;
no named participants or losses may be reconstructed from anonymous counts.
