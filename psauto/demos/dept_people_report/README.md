# Department people report (first half)

`GM_DEPT_RPT` is a physical SQL Table with one row per current primary job (`EMPL_RCD=0`) and department. `GM_DEPT_PAE` has two SQL steps: load the existing `GM_DEPT_TMP` snapshot, then insert current department/person/job rows into `%Table(GM_DEPT_RPT)`. The AE is saved and compiled only; execution and row-content validation are deliberately separate.

## 2026-11-07 object-only validation

The first-half demo was run through the generic PSIDE MCP and then checked with read-only DBX queries:

- `GM_DEPT_RPT`: saved, built and closed. DBX reports `RECTYPE=0`, 16 fields, seven key fields, `PS_GM_DEPT_RPT` in `HRAPP`, and one `VALID` unique index.
- `GM_DEPT_PAE`: saved, compiled and closed with `Disable Restart=Y`, default AET `GM_DEPT_AET`, and temporary record binding `GM_DEPT_TMP`. DBX reports `Step01` and `Step02` as SQL actions and the stored SQL matches this request.
- `GM_DEPT_PRT`: saved and closed. DBX reports 1,049 project members, including the AE, MAIN section, both SQL step members, and the three requested records/AET with their field members.

Native pipeline evidence is kept locally at `psauto/out/objects/20261107_061127_991894` (Record, 411 nodes/288.281 s), `psauto/out/objects/20261107_061904_163471` (AE, 105 nodes/77.344 s), and `psauto/out/objects/20261107_062057_922489` (Project, 87 nodes/64.532 s). All three returned `saved_and_closed`, `workspace_ready=true`, `evidence_status=complete`, and zero node/action failures. Candidate misses in the native summaries are normal recognition branches and did not fail a node.

Both physical tables currently contain zero rows. The AE was not scheduled or executed, so row contents, Process Scheduler permissions, and runtime SQL behavior remain unverified. A read-only data check found no `DEPTID` shared by multiple `SETID` values in `PS_DEPT_TBL`; the current Step02 join on `DEPTID` therefore has no collision in HRDEV, but this assumption should be rechecked in other environments.
