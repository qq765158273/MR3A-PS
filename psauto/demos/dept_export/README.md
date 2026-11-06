# Department export through a Temporary Table

This demo uses the generic PSIDE MCP operations:

1. `record_request.json` creates and builds `GM_DEPT_TMP` as a Temporary Table. It contains `PROCESS_INSTANCE` plus all 60 physical columns of `PS_DEPT_TBL`; `SETID`, `DEPTID`, and `EFFDT` remain keys.
2. `ae_request.json` creates `GM_DEPT_XL5`, binds `GM_DEPT_AET` and `GM_DEPT_TMP`, disables restart, then adds two steps:
   - Step01 SQL inserts every `PS_DEPT_TBL` row into `%Table(GM_DEPT_TMP)` with `%ProcessInstance`.
   - Step02 PeopleCode reads the current instance's temporary rows and writes the `.xlsx` through the existing `HpsReportDefn` helper.
3. `project_request.json` can be passed to `save_project` after both objects exist to package `GM_DEPT_XL5`, `GM_DEPT_TMP`, and the existing `GM_DEPT_AET` as `GM_DEPT_TEXP`.

The requests are API input, and the PeopleCode is kept separately for review (`export_peoplecode.pcode` and the explicitly named `temp_export_peoplecode.pcode`). The generic MCP currently creates new definitions and rejects duplicate names; it therefore creates `GM_DEPT_XL5` as the replacement sample while preserving the previously accepted `GM_DEPT_XL4`.

Creation/build success is verified by the Pipeline terminal state and DBX metadata. Actual Process Scheduler execution and workbook contents still require the matching PeopleTools Java/report runtime.

From `psauto/`, the three calls are:

```powershell
python call_mcp.py create_record --arguments demos/dept_export/record_request.json
python call_mcp.py create_ae --arguments demos/dept_export/ae_request.json
python call_mcp.py save_project --arguments demos/dept_export/project_request.json
```
