# GM_DEPT_PAE PSIDE runtime acceptance

The AE was run from PSIDE's **Edit → Run Program** dialog against HRDEV. No Process Scheduler request was created; the run was local to PSIDE.

The first run reached `MAIN.Step02` and rolled back with `ORA-01400` (RC 1400). The read-only data probe found one current primary job (`EMPLID=10004189`) without a row in `PS_PERSONAL_DATA`. Because Step02 used a `LEFT JOIN`, its three name expressions became NULL while `PS_GM_DEPT_RPT` requires those columns to be non-null. The original failure log is [first_failure_ora1400.png](first_failure_ora1400.png).

The SQL was corrected in PSIDE and saved with `NVL(P.NAME, ' ')`, `NVL(P.LAST_NAME, ' ')`, and `NVL(P.FIRST_NAME, ' ')`. The second PSIDE run ended normally; its log is [success_log.png](success_log.png). DBX then reported:

- Process instance `397099`, report rows `17,136`.
- Expected current-primary-job/dept join rows `17,136`; missing rows `0`; unexpected rows `0`.
- Duplicate report keys `0`; nullable target values `0`.
- The one missing-personal-data employee was retained with three single-space name values.

The run emitted warning `108,544`: no dedicated temporary-table instance was available, so PeopleTools used the `GM_DEPT_TMP` base table. The process still isolated by `PROCESS_INSTANCE` and cleaned the staging table after completion (`PS_GM_DEPT_TMP` row count `0`). For concurrent production scheduling, configure one or more temporary-table instances and recheck the allocation in DBX.
