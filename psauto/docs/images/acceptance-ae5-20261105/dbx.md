# GM_MCP_AE5 的 DBX 验收

2026-11-05，优化后的四步 AE 完整 MCP 调用返回 `saved_and_closed, workspace_ready:true` 后，通过 `ps-dev / HRDEV` 只读验收。AE 未执行。

## steps

```sql
SELECT AE_APPLID,AE_SECTION,AE_STEP,AE_SEQ_NUM FROM PSAESTEPDEFN WHERE AE_APPLID='GM_MCP_AE5' ORDER BY AE_SEQ_NUM
```

| AE_APPLID | AE_SECTION | AE_STEP | AE_SEQ_NUM |
|---|---|---|---|
| GM_MCP_AE5 | MAIN | Step01 | 1 |
| GM_MCP_AE5 | MAIN | Step02 | 2 |
| GM_MCP_AE5 | MAIN | Step03 | 3 |
| GM_MCP_AE5 | MAIN | Step04 | 4 |
(4 rows, 12ms)

## actions

```sql
SELECT S.AE_STEP,S.AE_STMT_TYPE,T.SQLTEXT FROM PSAESTMTDEFN S LEFT JOIN PSSQLTEXTDEFN T ON T.SQLID=S.SQLID WHERE S.AE_APPLID='GM_MCP_AE5' ORDER BY S.AE_STEP,S.AE_STMT_TYPE
```

| AE_STEP | AE_STMT_TYPE | SQLTEXT |
|---|---|---|
| Step01 | S | SELECT COUNT(*) FROM PS_GM_MCP_REC7 |
| Step02 | P | NULL |
| Step03 | S | SELECT COUNT(*) FROM PS_GM_MCP_REC7 |
| Step04 | P | NULL |
(4 rows, 15ms)

## peoplecode

```sql
SELECT OBJECTVALUE6 AS STEP_NAME,PCTEXT FROM PSPCMTXT WHERE OBJECTID1=66 AND OBJECTVALUE1='GM_MCP_AE5'
```

| STEP_NAME | PCTEXT |
|---|---|
| Step02 | Local SQL &fieldSQL;
Local string &fieldName;

&fieldSQL = CreateSQL("SELECT FIELDNAME FROM PSRECFIELD WHERE RECNAME = :1 ORDER BY FIELDNUM", "GM_MCP_REC7");
While &fieldSQL.Fetch(&fieldName)
   MessageBox(0, "", 0, 0, "FIELDNAME: " | &fieldName);
End-While;
&fieldSQL.Close();
 |
| Step04 | Local SQL &fieldSQL;
Local string &fieldName;

&fieldSQL = CreateSQL("SELECT FIELDNAME FROM PSRECFIELD WHERE RECNAME = :1 ORDER BY FIELDNUM", "GM_MCP_REC7");
While &fieldSQL.Fetch(&fieldName)
   MessageBox(0, "", 0, 0, "FIELDNAME: " | &fieldName);
End-While;
&fieldSQL.Close();
 |
(2 rows, 15ms)

## compiled

```sql
SELECT OBJECTVALUE6 AS STEP_NAME,PROGLEN FROM PSPCMPROG WHERE OBJECTID1=66 AND OBJECTVALUE1='GM_MCP_AE5'
```

| STEP_NAME | PROGLEN |
|---|---|
| Step02 | 566 |
| Step04 | 566 |
(2 rows, 13ms)
