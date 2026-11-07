# Department people report (first half)

`GM_DEPT_RPT` is a physical SQL Table with one row per current primary job (`EMPL_RCD=0`) and department. `GM_DEPT_PAE` has two SQL steps: load the existing `GM_DEPT_TMP` snapshot, then insert current department/person/job rows into `%Table(GM_DEPT_RPT)`. The AE is saved and compiled only; execution and row-content validation are deliberately separate.

## 2026-11-07 object-only validation

The first-half demo was run through the generic PSIDE MCP and then checked with read-only DBX queries:

- `GM_DEPT_RPT`: saved, built and closed. DBX reports `RECTYPE=0`, 16 fields, seven key fields, `PS_GM_DEPT_RPT` in `HRAPP`, and one `VALID` unique index.
- `GM_DEPT_PAE`: saved, compiled and closed with `Disable Restart=Y`, default AET `GM_DEPT_AET`, and temporary record binding `GM_DEPT_TMP`. DBX reports `Step01` and `Step02` as SQL actions and the stored SQL matches this request.
- `GM_DEPT_PRT`: saved and closed. DBX reports 1,049 project members, including the AE, MAIN section, both SQL step members, and the three requested records/AET with their field members.

Native pipeline evidence is kept locally at `psauto/out/objects/20261107_061127_991894` (Record, 411 nodes/288.281 s), `psauto/out/objects/20261107_061904_163471` (AE, 105 nodes/77.344 s), and `psauto/out/objects/20261107_062057_922489` (Project, 87 nodes/64.532 s). All three returned `saved_and_closed`, `workspace_ready=true`, `evidence_status=complete`, and zero node/action failures. Candidate misses in the native summaries are normal recognition branches and did not fail a node.

Before the runtime trial both physical tables were empty. A read-only data check found no `DEPTID` shared by multiple `SETID` values in `PS_DEPT_TBL`; the current Step02 join on `DEPTID` therefore has no collision in HRDEV, but this assumption should be rechecked in other environments. Process Scheduler registration and scheduling permissions remain outside this local PSIDE run.

## 2026-11-07 PSIDE runtime fix and recheck

The first PSIDE Run Program attempt reached Step02 but rolled back with `ORA-01400`: one current primary employee (`10004189`) has no `PS_PERSONAL_DATA` row, so the `LEFT JOIN` produced NULL names for non-null report columns. Step02 was repaired in PSIDE with `NVL(P.NAME, ' ')`, `NVL(P.LAST_NAME, ' ')`, and `NVL(P.FIRST_NAME, ' ')`. The second run ended normally with process instance `397099`. DBX matched all 17,136 expected department/primary-job keys exactly (0 missing, 0 extra, 0 duplicate), and the missing-personal-data employee was retained with single-space names. See [runtime evidence](../../docs/images/acceptance-dept-people-run-20261107/README.md).

The AE is now configured with the default `temporary_table_instances=3`. The temporary Record must be built before the AE is run; that Build generated `PS_GM_DEPT_TMP1` through `PS_GM_DEPT_TMP6` in this PeopleTools environment. A rerun ended normally with process instance `397101`, wrote the report rows, and retained the staging rows in the assigned instance `PS_GM_DEPT_TMP4` (`74,762` rows for that process instance). It did not clear the temporary data. The generated pool contains more physical tables than the configured count because PeopleTools reserves its own base/instance layout.
