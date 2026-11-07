# GM_DEPT_PAE PSIDE runtime acceptance

The AE was run from PSIDE's **Edit → Run Program** dialog against HRDEV. No Process Scheduler request was created; the run was local to PSIDE.

The first run reached `MAIN.Step02` and rolled back with `ORA-01400` (RC 1400). The read-only data probe found one current primary job (`EMPLID=10004189`) without a row in `PS_PERSONAL_DATA`. Because Step02 used a `LEFT JOIN`, its three name expressions became NULL while `PS_GM_DEPT_RPT` requires those columns to be non-null. The original failure log is [first_failure_ora1400.png](first_failure_ora1400.png).

The SQL was corrected in PSIDE and saved with `NVL(P.NAME, ' ')`, `NVL(P.LAST_NAME, ' ')`, and `NVL(P.FIRST_NAME, ' ')`. The second PSIDE run ended normally; its log is [success_log.png](success_log.png). DBX then reported:

- Process instance `397099`, report rows `17,136`.
- Expected current-primary-job/dept join rows `17,136`; missing rows `0`; unexpected rows `0`.
- Duplicate report keys `0`; nullable target values `0`.
- The one missing-personal-data employee was retained with three single-space name values.

The AE was then configured with `TEMPTBLINSTANCES=3` in PSIDE. Building `GM_DEPT_TMP` first generated `PS_GM_DEPT_TMP1` through `PS_GM_DEPT_TMP6`, each with a VALID unique index. A rerun ended normally (log: [success_log_instances3.png](success_log_instances3.png)); DBX identified process instance `397101`, report rows `17,136`, and staging rows in the assigned `PS_GM_DEPT_TMP4` instance (`74,762` rows for that process instance). The staging rows remain available for post-run inspection; the AE SQL does not truncate them. The extra physical tables are PeopleTools' base/instance pool layout, not six requested logical instances.

The MCP request now defaults to `temporary_table_instances=3`. A Temporary Table must be built before execution so the physical instance pool exists; setting the AE property alone is insufficient and produced the observed `ORA-00942` on `PS_GM_DEPT_TMP4` before the Build.
