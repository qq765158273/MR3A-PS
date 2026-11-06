# 部门临时表AE业务只读审核

完成时间：2026-11-06 03:03:40 UTC（UTC；北京时间加8小时）。轮次 `department-temp-5a9ce42-20261106`。主控ps，复核pshelp，回复目标ps:0.0。

仓库 `C:/Users/t-wangsen05/Desktop/MR3A-PS`；origin `https://github.com/qq765158273/MR3A-PS`；分支 `feat/psauto-jumpserver`；基线/读取时HEAD `5a9ce4218cf9ad74aa4fdc93f7a495713a66f95e`。只审本轮五份未提交业务输入，没有修改它们，也未审查或重跑旧Pipeline。没有浏览器操作、AE执行、编译提交、DDL/DML、对象创建或commit；只有DBX只读SELECT、外部文档只读获取及本地内存解析。仓库内仅写本报告。

**结论：五份输入内部一致，61字段/四键、全量INSERT SELECT、60列导出顺序及按进程号查询的静态设计满足本轮需求，未发现证据充分的确定P1错误。P2为文件完成验收仍仅检查存在性；这是保护缺口，未复现实际坏工作簿。临时表、AE和Project尚无本轮最终保存/编译/运行验收，本报告不把请求JSON或旧样本当作实际对象成功。已有JVM问题仍阻断Excel运行结论。**

## 输入身份和核验方法

以下是工作区原始字节SHA-256，非Git规范化换行后的blob ID。首次读取北京时间10:58:28，结束前11:02左右复算均未变。

```text
1fc59282ad40320220c8ea37c55595ef262ec5fc66d9d6874c812b4adbf38864  psauto/demos/dept_export/record_request.json
42e549aea09621be514cf0fe5b6f12b8aa48575f44b1ff084b695ecd0aab150b  psauto/demos/dept_export/ae_request.json
c54185fadc58a1e434a8ab968fb621d233ab6731e4e46349690534b870f5a6c5  psauto/demos/dept_export/step01_insert.sql
3790fe8b6ce12374df0934ef37b3920df0b6a528f3ab92f76ce5b826c7895406  psauto/demos/dept_export/temp_export_peoplecode.pcode
b020505f882ebc26f99ccd0dcf1f28ba1c47115e961608d6ea1ded886a0d8cd3  psauto/demos/dept_export/project_request.json
```

独立解析三份JSON和两个源码文件，未调用业务构建器或编译器。实际结果：

- Record共61个字段且无重复，顺序为PROCESS_INSTANCE＋源表60列；键只有PROCESS_INSTANCE/SETID/DEPTID/EFFDT，顺序与要求一致。Temporary Table、build:true、HRAPP明确。
- INSERT目标61列，SELECT为%ProcessInstance＋60列；三方顺序一致。源无WHERE、JOIN、DISTINCT、聚合或有效日期筛选，不会主动删去无效/历史行。
- PeopleCode表头60列、SELECT投影60列，与Record去掉PROCESS_INSTANCE后的顺序完全相同；再与本次USER_TAB_COLUMNS的60个物理列逐项比较也相同。
- ae_request中的Step01正文与step01_insert.sql只差文件末尾分号/空白；Step02正文与独立PeopleCode文件在CRLF/LF规范化后完全相同。不能把原始字节换行差当成业务不一致。
- AE请求是SQL→PeopleCode两个步骤，名字GM_DEPT_XL5、默认GM_DEPT_AET、disable_restart:true、temporary_records=[GM_DEPT_TMP]。Project请求GM_DEPT_TEXP显式包含这三个业务定义。
- 这些是独立内存结构核对，不能称作PeopleCode编译、MetaSQL运行或Excel测试通过。本轮没有执行native视觉测试，也不累计旧测试数。

## 数据库只读实测及时间边界

查询连接为DBX ps-dev/HRDEV；内部DB_NAME=CDBHCM、CURRENT_SCHEMA=SYSADM。首次数据库时间为 **2026-11-06 10:58:51.73356 +08:00**。下面所有SQL、返回和各次UTC时间完整嵌入文末，未另写未经授权的证据文件夹。

1. PS_DEPT_TBL有60物理列，本次快照74762行，A=60336、I=14426，(SETID,DEPTID,EFFDT)重复组为0。数字字段当前范围：BUDGET_YR_END_DT=0，APS_AGENT_CD_AUS=0，HPS_DEPT_BUD_NUM为0至10007068，均在既有字段4/3/8位整数定义内。74762不是未来常数。
2. 请求的61个PSDBFIELD均存在。源字符列与字段长度比较没有短定义；PROCESS_INSTANCE是Number(10,0)，EFFDT为Date，LASTUPDDTTM为DateTime，BJ_DEPT_RESP为LongCharacter(500)，不是把后者误当短字符。此处验证的是定义可引用，不是生成表的实际Oracle类型/NULL约束。
3. 已存在GM_DEPT_AET为Derived/Work、两字段：PROCESS_INSTANCE Number(10,0)、FILE_NAME Character(80)。本次文件名最长43字符，未发现这80字符字段会截断当前模式；完整路径另需运行环境验证。
4. **10:58:52快照中PSRECDEFN无GM_DEPT_TMP、无GM_DEPT_XL5 AE；11:00:53查询无PS_GM_DEPT_TMP及编号实例物理表。** 主控当时正在独占创建流程，这只是采样时状态，不能当作流程失败，也不能等后续可能创建后反向声称此刻已验收。未轮询或等待创建完成。
5. 引用helper HPS_RPT_FUNC_WK.FUNCLIB_01.FieldFormula仍存在，PROGSEQ=0、5099字符、HASH_SIGNATURE=aYDNkTbDAsGejVbDsPeIN5iNMX4A。本次直接查询的源码尾部确认buildJavaArray(array of any)分配java.lang.String[]并逐元素反射set。没有取得部署HpsReportDefn的class/JAR，没有运行Java。

目标AE尚未创建，故本轮不能查询并重建它的PSPCMTXT来证明实际保存源码身份，也不能核对真正编译长度、MAIN两个动作的最终状态、Disable Restart或临时表实际绑定。**本轮源码真源仅限上列五份指定文件的SHA；库中既有helper和源表元数据是独立DB证据。**

## MetaSQL、进程号和隔离判断

[step01_insert.sql:1](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/demos/dept_export/step01_insert.sql:1)将%ProcessInstance放在AE **SQL动作**的SELECT第一项；这是AE MetaSQL位置，不能套用前轮“PeopleCode里无效的%ProcessInstance系统变量”结论。Step02在[第13行](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/demos/dept_export/temp_export_peoplecode.pcode:13)从绑定AET取PROCESS_INSTANCE，在[第29行](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/demos/dept_export/temp_export_peoplecode.pcode:29)以数值bind `:1` 过滤；没有把该值直接拼到SQL文本，也没有无条件读整张共享临时基表。

两步均使用 `%Table(GM_DEPT_TMP)`，没有一处硬编码 `PS_GM_DEPT_TMP` 或编号后缀。官方[MetaSQL参考](https://docs.oracle.com/cd/E24150_01/pt851h2/eng/psbooks/tpcl/htm/tpcl03.htm)解释：当前进程若获分配临时表实例，%Table解析到该实例；也可在PeopleCode SQL上下文使用。该已读取文档为8.51语义参考，**不是本机8.57/本AE的实际展开证据**；运行验收仍应查SQL trace，确认SQL动作和CreateSQL解析到同一个物理实例。

在同一AE上下文、有效temp binding和系统正确初始化AET的前提下，SQL动作%ProcessInstance与AET.PROCESS_INSTANCE应一致，四键允许不同进程有同一SETID/DEPTID/EFFDT，Step02只读本进程。没看到缺少进程号条件或读错固定编号表的确定错误。下列边界未实测：

- 分配了哪个实例、实例数、实例不足时Abort/Continue以及退回共享基表的实际配置；主控创建后还需核对。
- 不允许未核实AET进程号一致性就把“WHERE存在”写成真实并发隔离已通过；若值不一致，查询可能为零行。
- 正常临时表分配/清理应遵循AE机制。源码未显式DELETE，不足以证明一定脏读或键冲突；若以后允许同一进程号重复执行Step01且同一物理表有旧行，可能因四键重复而拒绝。Disable Restart不保证外部重复调用幂等，但本轮没有该重放路径/证据。
- 对退回共享基表的情形，不应为了“清理”无条件TRUNCATE全表；若需应用级清理，应按本实例和受控生命周期设计。

## PeopleCode可编译性与数据契约

从静态语法和现有引用看，array of any接Fetch、长度检查60、header和row交给已存在的buildJavaArray，没有发现明显声明/参数矛盾。String[]可作为Java Object[]的子类型；**不能据此保证PeopleCode到部署Java重载一定可用**，更不能保证HpsReportDefn内部使用XSSF/SXSSF而非HSSF。没有运行PSIDE编译、AE或Java，此项为静态判断，不是“可编译已实测”。

- 60列导出故意不包含临时表自己的PROCESS_INSTANCE，符合“PROCESS_INSTANCE用于隔离，导出源表60列”。
- Step01不格式化日期，而是按原Oracle值入临时表；Step02才把EFFDT转YYYY-MM-DD、LASTUPDDTTM转YYYY-MM-DD HH24:MI:SS.FF6。方向正确，但生成表中LASTUPDDTTM必须实际是TIMESTAMP(6)，不能只凭PSDBFIELD DateTime断言建表结果绝不降精度。
- 当前源LASTUPDDTTM/BJ_DEPT_RESP无NULL，未测试NULL路径。新注释“nulls as empty cells”只是意图，PeopleCode/Java完整链没有运行；生成表NULL约束与源也应核对。
- 全部值拼接空字符串后进入String[]，不会在该helper主动按数字猜测；但数字单元格、NULL/空白与前导零最终写法须由实际工作簿确定。没有用户要求数值单元格的证据，不能把全文本策略直接判错。
- 已把旧固定日志标签换成program=GM_DEPT_XL5，在当前输入静态修正了旧样本误标签问题；不表示旧部署XL4已改。
- Project逻辑范围包含AE、临时Record及AET；既有源表/helper/JAR是前置依赖，不是这三个成员就构成自包含可运行迁移包。

## P1/P2发现与触发条件

**未发现本轮静态和只读查询能确定的P1代码阻断。** 当前实际表/AE未完成及旧JVM问题是创建/编译/运行验收边界，不能硬判成这五份业务输入错误。

### P2：FileExists只确认存在，仍可把无效文件报告COMPLETE

位置：[temp_export_peoplecode.pcode:46](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/demos/dept_export/temp_export_peoplecode.pcode:46)、[第48行](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/demos/dept_export/temp_export_peoplecode.pcode:48)、[第51行](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/demos/dept_export/temp_export_peoplecode.pcode:51)；ae_request的第二个code含相同正文。

比旧草稿已增加不存在文件即Error，改善明确；但FileExists为true就继续COMPLETE，没有文件长度、可打开性、ZIP/OOXML结构、sheet列数/行数判决，也无临时文件成功发布和失败后半成品处置。

**触发条件：** generateExcel静默返回但留下零字节/截断/错误格式文件，或输出路径已存在旧文件而本次未正确重写；FileExists仍可能为true。若方法写了一部分后抛异常，程序不会发COMPLETE，但业务层也没有自己的半成品隔离路径。Java是否内部已经原子发布/清理尚未知，所以这是**可确定的业务层验收保护缺口，非已运行复现的坏Excel或已证实Java缺陷**。不能据未捕获异常推断AE会吞错、SQL句柄一定泄漏；Derived/Work FILE_NAME也不会仅因赋值就持久写回数据库。

建议先查组件文件契约，再按需求加生成后可读/结构检查、明确成功/失败日志及临时文件发布/清理。单纯FileExists无法完成“真正可打开xlsx”的需求验收。本轮没有修改代码或制造磁盘故障。

## 其他风险和建议顺序

1. **先验收新物理表，而非等待Excel。** 主控创建完成后核对61列及精度/NULL约束、四键唯一索引和HRAPP，尤其LASTUPDDTTM TIMESTAMP(6)、LongCharacter BJ_DEPT_RESP。再核对AE两步正文全部PROGSEQ、默认AET、temp binding和Disable Restart。创建/编译不能当运行成功。
2. **再核实运行前置。** 用户优先PSIDE直接Run；只读取得匹配64位JVM/HPS/POI类版本和方法/格式证据，旧JVM启动失败不能精确等价于“未安装”，也不必把PIA可达当作PSIDE Run必要条件。本轮不安装、不改环境、不运行。
3. **运行时完整性。** 正式获授权运行后，保存SQL trace中%Table和进程号展开、Step01影响行数、Step02抓取行数与文件实际行数。同一个快照口径比对，不硬编码74762。合法空源数据可以导出零行，不能简单加“rows=0必错”；若本次插入计数非零而查询为零则应拒绝成功。
4. **文件/性能验收。** 74762行正文×60列为4485720单元格，含表头74763行已超过xls单表限制。新增临时表阶段不自动消除Java单元格构造和可能的内存成本。没有JAR实现/运行剖析，不能断言report一定全部驻留内存或此次一定OOM；应测实际格式、sheet维度、中文/零前缀/NULL/6位小数、峰值内存和耗时，并保留失败原样。xlsx也有单sheet上限，不能宣称无限行数。
5. 物理表/AE创建验收和最终Excel业务验收分开记录；本轮没有必要重跑或重审旧61字段视觉Pipeline。

## 尚未验证

实际GM_DEPT_TMP的最终列/键/索引/实例和Build结果；GM_DEPT_XL5保存源码、编译及属性；运行时MetaSQL实际展开、AET进程号、并发/回退基表/中断清理；真正xlsx、Java方法/格式、大行数/内存、路径权限/磁盘满、NULL和数值文本契约；Project实际保存成员。主控后续运行不属于本报告收尾阻塞，本报告保留这些未完成项，不等待或操作其业务环境。

## 只读查询原始证据（时间为UTC）

以下是本agent本轮直接执行的只读SQL及原始DBX返回，不是转述主控旧结论。全部采样发生在创建过程中，不能作为之后最终状态。

### identity — 2026-11-06 02:58:52 UTC

```sql
SELECT SYS_CONTEXT('USERENV','DB_NAME') AS DB_NAME,SYS_CONTEXT('USERENV','CURRENT_SCHEMA') AS CURRENT_SCHEMA,SYSTIMESTAMP AS QUERY_TIME FROM DUAL;
```

```text
| DB_NAME | CURRENT_SCHEMA | QUERY_TIME |
|---|---|---|
| CDBHCM | SYSADM | 2026-11-06T10:58:51.73356+08:00 |
(1 rows, 14ms)
```

### source_columns — 2026-11-06 02:58:52 UTC

```sql
SELECT COLUMN_ID,COLUMN_NAME,DATA_TYPE,CHAR_LENGTH,DATA_PRECISION,DATA_SCALE,NULLABLE FROM USER_TAB_COLUMNS WHERE TABLE_NAME='PS_DEPT_TBL' ORDER BY COLUMN_ID;
```

```text
| COLUMN_ID | COLUMN_NAME | DATA_TYPE | CHAR_LENGTH | DATA_PRECISION | DATA_SCALE | NULLABLE |
|---|---|---|---|---|---|---|
| 1 | SETID | VARCHAR2 | 5 | NULL | NULL | N |
| 2 | DEPTID | VARCHAR2 | 10 | NULL | NULL | N |
| 3 | EFFDT | DATE | 0 | NULL | NULL | N |
| 4 | EFF_STATUS | VARCHAR2 | 1 | NULL | NULL | N |
| 5 | DESCR | VARCHAR2 | 30 | NULL | NULL | N |
| 6 | DESCRSHORT | VARCHAR2 | 10 | NULL | NULL | N |
| 7 | COMPANY | VARCHAR2 | 3 | NULL | NULL | N |
| 8 | SETID_LOCATION | VARCHAR2 | 5 | NULL | NULL | N |
| 9 | LOCATION | VARCHAR2 | 10 | NULL | NULL | N |
| 10 | TAX_LOCATION_CD | VARCHAR2 | 10 | NULL | NULL | N |
| 11 | MANAGER_ID | VARCHAR2 | 11 | NULL | NULL | N |
| 12 | MANAGER_POSN | VARCHAR2 | 8 | NULL | NULL | N |
| 13 | BUDGET_YR_END_DT | NUMBER | 0 | NULL | 0 | N |
| 14 | BUDGET_LVL | VARCHAR2 | 1 | NULL | NULL | N |
| 15 | GL_EXPENSE | VARCHAR2 | 35 | NULL | NULL | N |
| 16 | EEO4_FUNCTION | VARCHAR2 | 2 | NULL | NULL | N |
| 17 | CAN_IND_SECTOR | VARCHAR2 | 3 | NULL | NULL | N |
| 18 | ACCIDENT_INS | VARCHAR2 | 15 | NULL | NULL | N |
| 19 | SI_ACCIDENT_NUM | VARCHAR2 | 15 | NULL | NULL | N |
| 20 | HAZARD | VARCHAR2 | 8 | NULL | NULL | N |
| 21 | ESTABID | VARCHAR2 | 12 | NULL | NULL | N |
| 22 | RISKCD | VARCHAR2 | 6 | NULL | NULL | N |
| 23 | GVT_DESCR40 | VARCHAR2 | 40 | NULL | NULL | N |
| 24 | GVT_SUB_AGENCY | VARCHAR2 | 2 | NULL | NULL | N |
| 25 | GVT_PAR_LINE2 | VARCHAR2 | 10 | NULL | NULL | N |
| 26 | GVT_PAR_LINE3 | VARCHAR2 | 10 | NULL | NULL | N |
| 27 | GVT_PAR_LINE4 | VARCHAR2 | 10 | NULL | NULL | N |
| 28 | GVT_PAR_LINE5 | VARCHAR2 | 10 | NULL | NULL | N |
| 29 | GVT_PAR_DESCR2 | VARCHAR2 | 40 | NULL | NULL | N |
| 30 | GVT_PAR_DESCR3 | VARCHAR2 | 40 | NULL | NULL | N |
| 31 | GVT_PAR_DESCR4 | VARCHAR2 | 40 | NULL | NULL | N |
| 32 | GVT_PAR_DESCR5 | VARCHAR2 | 40 | NULL | NULL | N |
| 33 | FTE_EDIT_INDC | VARCHAR2 | 1 | NULL | NULL | N |
| 34 | DEPT_TENURE_FLG | VARCHAR2 | 1 | NULL | NULL | N |
| 35 | TL_DISTRIB_INFO | VARCHAR2 | 1 | NULL | NULL | N |
| 36 | USE_BUDGETS | VARCHAR2 | 1 | NULL | NULL | N |
| 37 | USE_ENCUMBRANCES | VARCHAR2 | 1 | NULL | NULL | N |
| 38 | USE_DISTRIBUTION | VARCHAR2 | 1 | NULL | NULL | N |
| 39 | BUDGET_DEPTID | VARCHAR2 | 10 | NULL | NULL | N |
| 40 | HP_STATS_DEPT_CD | VARCHAR2 | 3 | NULL | NULL | N |
| 41 | HP_STATS_DPCD_NW | VARCHAR2 | 2 | NULL | NULL | N |
| 42 | HP_STATS_FACULTY | VARCHAR2 | 5 | NULL | NULL | N |
| 43 | MANAGER_NAME | VARCHAR2 | 30 | NULL | NULL | N |
| 44 | ACCOUNTING_OWNER | VARCHAR2 | 30 | NULL | NULL | N |
| 45 | COUNTRY_GRP | VARCHAR2 | 18 | NULL | NULL | N |
| 46 | HP_RTBC_OPTION | VARCHAR2 | 1 | NULL | NULL | N |
| 47 | HP_AUTO_RTBC | VARCHAR2 | 1 | NULL | NULL | N |
| 48 | CLASS_UNIT_NZL | VARCHAR2 | 5 | NULL | NULL | N |
| 49 | ORG_UNIT_AUS | VARCHAR2 | 4 | NULL | NULL | N |
| 50 | WORK_SECTOR_AUS | VARCHAR2 | 1 | NULL | NULL | N |
| 51 | APS_AGENT_CD_AUS | NUMBER | 0 | NULL | 0 | N |
| 52 | IND_COMMITTEE_BEL | VARCHAR2 | 3 | NULL | NULL | N |
| 53 | NACE_CD_BEL | VARCHAR2 | 10 | NULL | NULL | N |
| 54 | LASTUPDDTTM | TIMESTAMP(6) | 0 | NULL | 6 | Y |
| 55 | HPS_ROOT_NODE | VARCHAR2 | 1 | NULL | NULL | N |
| 56 | HPS_DEPT_LVL | VARCHAR2 | 2 | NULL | NULL | N |
| 57 | HPS_DEPT_BUD_NUM | NUMBER | 0 | NULL | 0 | N |
| 58 | HPS_ORG_STRUCTURE | VARCHAR2 | 150 | NULL | NULL | N |
| 59 | BJ_HRBP_ID | VARCHAR2 | 11 | NULL | NULL | N |
| 60 | BJ_DEPT_RESP | VARCHAR2 | 500 | NULL | NULL | Y |
(60 rows, 422ms)
```

### source_stats — 2026-11-06 02:58:52 UTC

```sql
SELECT COUNT(*) AS ROW_COUNT,SUM(CASE WHEN EFF_STATUS='A' THEN 1 ELSE 0 END) AS ACTIVE_ROWS,SUM(CASE WHEN EFF_STATUS='I' THEN 1 ELSE 0 END) AS INACTIVE_ROWS,SUM(CASE WHEN LASTUPDDTTM IS NULL THEN 1 ELSE 0 END) AS LASTUPD_NULLS,SUM(CASE WHEN BJ_DEPT_RESP IS NULL THEN 1 ELSE 0 END) AS RESP_NULLS FROM PS_DEPT_TBL;
```

```text
| ROW_COUNT | ACTIVE_ROWS | INACTIVE_ROWS | LASTUPD_NULLS | RESP_NULLS |
|---|---|---|---|---|
| 74762 | 60336 | 14426 | 0 | 0 |
(1 rows, 95ms)
```

### object_state — 2026-11-06 02:58:52 UTC

```sql
SELECT RECNAME,RECTYPE,FIELDCOUNT,INDEXCOUNT,LASTUPDDTTM FROM PSRECDEFN WHERE RECNAME IN ('GM_DEPT_TMP','GM_DEPT_AET') ORDER BY RECNAME;
```

```text
| RECNAME | RECTYPE | FIELDCOUNT | INDEXCOUNT | LASTUPDDTTM |
|---|---|---|---|---|
| GM_DEPT_AET | 2 | 2 | 0 | 2026-11-05T19:52:22.82682 |
(1 rows, 14ms)
```

### aet_fields — 2026-11-06 02:58:52 UTC

```sql
SELECT R.RECNAME,R.FIELDNUM,R.FIELDNAME,R.USEEDIT,F.FIELDTYPE,F.LENGTH,F.DECIMALPOS FROM PSRECFIELD R JOIN PSDBFIELD F ON F.FIELDNAME=R.FIELDNAME WHERE R.RECNAME='GM_DEPT_AET' ORDER BY R.FIELDNUM;
```

```text
| RECNAME | FIELDNUM | FIELDNAME | USEEDIT | FIELDTYPE | LENGTH | DECIMALPOS |
|---|---|---|---|---|---|---|
| GM_DEPT_AET | 1 | PROCESS_INSTANCE | 8388608 | 2 | 10 | 0 |
| GM_DEPT_AET | 2 | FILE_NAME | 8388608 | 0 | 80 | 0 |
(2 rows, 20ms)
```

### target_ae — 2026-11-06 02:58:52 UTC

```sql
SELECT A.AE_APPLID,A.AE_DISABLE_RESTART,S.AE_STATE_RECNAME,S.AE_DEFAULT_STATE FROM PSAEAPPLDEFN A LEFT JOIN PSAEAPPLSTATE S ON S.AE_APPLID=A.AE_APPLID WHERE A.AE_APPLID='GM_DEPT_XL5';
```

```text
| AE_APPLID | AE_DISABLE_RESTART | AE_STATE_RECNAME | AE_DEFAULT_STATE |
|---|---|---|---|
(0 rows, 12ms)
```

### source_key — 2026-11-06 02:58:52 UTC

```sql
SELECT COUNT(*) AS DUPLICATE_KEY_GROUPS FROM (SELECT SETID,DEPTID,EFFDT,COUNT(*) C FROM PS_DEPT_TBL GROUP BY SETID,DEPTID,EFFDT HAVING COUNT(*)>1);
```

```text
| DUPLICATE_KEY_GROUPS |
|---|
| 0 |
(1 rows, 43ms)
```

### helper — 2026-11-06 02:58:52 UTC

```sql
SELECT OBJECTID1,OBJECTVALUE1,OBJECTVALUE2,OBJECTVALUE3,PROGSEQ,HASH_SIGNATURE,DBMS_LOB.GETLENGTH(PCTEXT) AS SOURCE_CHARS,DBMS_LOB.SUBSTR(PCTEXT,1800,4001) AS HELPER_TAIL FROM PSPCMTXT WHERE OBJECTID1=1 AND OBJECTVALUE1='HPS_RPT_FUNC_WK' AND OBJECTVALUE2='FUNCLIB_01' AND OBJECTVALUE3='FieldFormula' ORDER BY PROGSEQ;
```

```text
| OBJECTID1 | OBJECTVALUE1 | OBJECTVALUE2 | OBJECTVALUE3 | PROGSEQ | HASH_SIGNATURE | SOURCE_CHARS | HELPER_TAIL |
|---|---|---|---|---|---|---|---|
| 1 | HPS_RPT_FUNC_WK | FUNCLIB_01 | FieldFormula | 0 | aYDNkTbDAsGejVbDsPeIN5iNMX4A | 5099 | ArrayClass.set(&jStrs, &i - 1, Value(&aStrs [&i]));

            rem 新代码;
            If Upper(&number1) <> "E" Then
               &jArrayClass.set(&jStrs, &i - 1, Value(&aStrs [&i]));
            Else
               &jArrayClass.set(&jStrs, &i - 1, &aStrs [&i]);
            End-If;
            /*end:modify by Ljj 2020-05-14 对于E或e开头的数据进行处理*/
         End-If;

      Else
         &jArrayClass.set(&jStrs, &i - 1, &aStrs [&i]);
      End-If;

   End-For;


   /*modify by zl 修改数字类型科学计数法问题 end*/
   /*---------------------------------------------*/

   Return &jStrs;
End-Function;


rem 字符串项写入;
Function buildJavaArray(&aStrs As array of any) Returns JavaObject
   Local JavaObject &jStrs;
   Local JavaObject &jArrayClass;
   Local integer &i;

   &jArrayClass = GetJavaClass("java.lang.reflect.Array");
   &jStrs = CreateJavaArray("java.lang.String[]", &aStrs.Len);

   For &i = 1 To &aStrs.Len
      &jArrayClass.set(&jStrs, &i - 1, &aStrs [&i]);
   End-For;

   Return &jStrs;
End-Function;

/*add by zhaixm 2020-04-28 project:HPS_PY_RPT_004 end*/
 |
(1 rows, 21ms)
```

### field_definitions — 2026-11-06 03:00:03 UTC

```sql
SELECT FIELDNAME,FIELDTYPE,LENGTH,DECIMALPOS FROM PSDBFIELD WHERE FIELDNAME IN ('PROCESS_INSTANCE','SETID','DEPTID','EFFDT','EFF_STATUS','DESCR','DESCRSHORT','COMPANY','SETID_LOCATION','LOCATION','TAX_LOCATION_CD','MANAGER_ID','MANAGER_POSN','BUDGET_YR_END_DT','BUDGET_LVL','GL_EXPENSE','EEO4_FUNCTION','CAN_IND_SECTOR','ACCIDENT_INS','SI_ACCIDENT_NUM','HAZARD','ESTABID','RISKCD','GVT_DESCR40','GVT_SUB_AGENCY','GVT_PAR_LINE2','GVT_PAR_LINE3','GVT_PAR_LINE4','GVT_PAR_LINE5','GVT_PAR_DESCR2','GVT_PAR_DESCR3','GVT_PAR_DESCR4','GVT_PAR_DESCR5','FTE_EDIT_INDC','DEPT_TENURE_FLG','TL_DISTRIB_INFO','USE_BUDGETS','USE_ENCUMBRANCES','USE_DISTRIBUTION','BUDGET_DEPTID','HP_STATS_DEPT_CD','HP_STATS_DPCD_NW','HP_STATS_FACULTY','MANAGER_NAME','ACCOUNTING_OWNER','COUNTRY_GRP','HP_RTBC_OPTION','HP_AUTO_RTBC','CLASS_UNIT_NZL','ORG_UNIT_AUS','WORK_SECTOR_AUS','APS_AGENT_CD_AUS','IND_COMMITTEE_BEL','NACE_CD_BEL','LASTUPDDTTM','HPS_ROOT_NODE','HPS_DEPT_LVL','HPS_DEPT_BUD_NUM','HPS_ORG_STRUCTURE','BJ_HRBP_ID','BJ_DEPT_RESP') ORDER BY FIELDNAME;
```

```text
| FIELDNAME | FIELDTYPE | LENGTH | DECIMALPOS |
|---|---|---|---|
| ACCIDENT_INS | 0 | 15 | 0 |
| ACCOUNTING_OWNER | 0 | 30 | 0 |
| APS_AGENT_CD_AUS | 2 | 3 | 0 |
| BJ_DEPT_RESP | 1 | 500 | 0 |
| BJ_HRBP_ID | 0 | 11 | 0 |
| BUDGET_DEPTID | 0 | 10 | 0 |
| BUDGET_LVL | 0 | 1 | 0 |
| BUDGET_YR_END_DT | 2 | 4 | 0 |
| CAN_IND_SECTOR | 0 | 3 | 0 |
| CLASS_UNIT_NZL | 0 | 5 | 0 |
| COMPANY | 0 | 3 | 0 |
| COUNTRY_GRP | 0 | 18 | 0 |
| DEPTID | 0 | 10 | 0 |
| DEPT_TENURE_FLG | 0 | 1 | 0 |
| DESCR | 0 | 30 | 0 |
| DESCRSHORT | 0 | 10 | 0 |
| EEO4_FUNCTION | 0 | 2 | 0 |
| EFFDT | 4 | 10 | 0 |
| EFF_STATUS | 0 | 1 | 0 |
| ESTABID | 0 | 12 | 0 |
| FTE_EDIT_INDC | 0 | 1 | 0 |
| GL_EXPENSE | 0 | 35 | 0 |
| GVT_DESCR40 | 0 | 40 | 0 |
| GVT_PAR_DESCR2 | 0 | 40 | 0 |
| GVT_PAR_DESCR3 | 0 | 40 | 0 |
| GVT_PAR_DESCR4 | 0 | 40 | 0 |
| GVT_PAR_DESCR5 | 0 | 40 | 0 |
| GVT_PAR_LINE2 | 0 | 10 | 0 |
| GVT_PAR_LINE3 | 0 | 10 | 0 |
| GVT_PAR_LINE4 | 0 | 10 | 0 |
| GVT_PAR_LINE5 | 0 | 10 | 0 |
| GVT_SUB_AGENCY | 0 | 2 | 0 |
| HAZARD | 0 | 8 | 0 |
| HPS_DEPT_BUD_NUM | 2 | 8 | 0 |
| HPS_DEPT_LVL | 0 | 2 | 0 |
| HPS_ORG_STRUCTURE | 0 | 150 | 0 |
| HPS_ROOT_NODE | 0 | 1 | 0 |
| HP_AUTO_RTBC | 0 | 1 | 0 |
| HP_RTBC_OPTION | 0 | 1 | 0 |
| HP_STATS_DEPT_CD | 0 | 3 | 0 |
| HP_STATS_DPCD_NW | 0 | 2 | 0 |
| HP_STATS_FACULTY | 0 | 5 | 0 |
| IND_COMMITTEE_BEL | 0 | 3 | 0 |
| LASTUPDDTTM | 6 | 26 | 0 |
| LOCATION | 0 | 10 | 0 |
| MANAGER_ID | 0 | 11 | 0 |
| MANAGER_NAME | 0 | 30 | 0 |
| MANAGER_POSN | 0 | 8 | 0 |
| NACE_CD_BEL | 0 | 10 | 0 |
| ORG_UNIT_AUS | 0 | 4 | 0 |
| PROCESS_INSTANCE | 2 | 10 | 0 |
| RISKCD | 0 | 6 | 0 |
| SETID | 0 | 5 | 0 |
| SETID_LOCATION | 0 | 5 | 0 |
| SI_ACCIDENT_NUM | 0 | 15 | 0 |
| TAX_LOCATION_CD | 0 | 10 | 0 |
| TL_DISTRIB_INFO | 0 | 1 | 0 |
| USE_BUDGETS | 0 | 1 | 0 |
| USE_DISTRIBUTION | 0 | 1 | 0 |
| USE_ENCUMBRANCES | 0 | 1 | 0 |
| WORK_SECTOR_AUS | 0 | 1 | 0 |
(61 rows, 23ms)
```

### numeric_bounds — 2026-11-06 03:00:53 UTC

```sql
SELECT MIN(BUDGET_YR_END_DT) AS MIN_BUDGET_YEAR,MAX(BUDGET_YR_END_DT) AS MAX_BUDGET_YEAR,MIN(APS_AGENT_CD_AUS) AS MIN_APS,MAX(APS_AGENT_CD_AUS) AS MAX_APS,MIN(HPS_DEPT_BUD_NUM) AS MIN_BUD_NUM,MAX(HPS_DEPT_BUD_NUM) AS MAX_BUD_NUM FROM PS_DEPT_TBL;
```

```text
| MIN_BUDGET_YEAR | MAX_BUDGET_YEAR | MIN_APS | MAX_APS | MIN_BUD_NUM | MAX_BUD_NUM |
|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 | 10007068 |
(1 rows, 30ms)
```

### physical_temp_state — 2026-11-06 03:00:53 UTC

```sql
SELECT TABLE_NAME,COLUMN_ID,COLUMN_NAME,DATA_TYPE,CHAR_LENGTH,NULLABLE FROM USER_TAB_COLUMNS WHERE TABLE_NAME='PS_GM_DEPT_TMP' ORDER BY COLUMN_ID;
```

```text
| TABLE_NAME | COLUMN_ID | COLUMN_NAME | DATA_TYPE | CHAR_LENGTH | NULLABLE |
|---|---|---|---|---|---|
(0 rows, 380ms)
```

### temp_instances — 2026-11-06 03:00:53 UTC

```sql
SELECT TABLE_NAME FROM USER_TABLES WHERE TABLE_NAME='PS_GM_DEPT_TMP' OR REGEXP_LIKE(TABLE_NAME,'^PS_GM_DEPT_TMP[0-9]+$') ORDER BY TABLE_NAME;
```

```text
| TABLE_NAME |
|---|
(0 rows, 402ms)
```


## 编译阻断定向更正附记 — 2026-11-06 03:27:33 UTC（UTC；北京时间加8小时）

本段只处理主控新提供的两个真实编译错误，**不重审前轮Pipeline或重跑整轮业务审核**。原11:03:40报告及五SHA保留历史。**初审静态检查漏掉了下面两项编译阻断；“未发现确定P1”不能继续作为原稿可交付的结论。** 本次已确认原稿存在P1编译错误；当前修订稿在两个对应静态条件上已修正，仍须主控实际重新编译，未被本agent计作编译/运行通过。

### P1-1：原稿把多变量声明与初始化混在同一条Local中

原稿第11行（冻结的[失败请求](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/out/objects/20261106_111613_013751/request.json)中的Step02）为：

```peoplecode
Local string &filename, &path, &program = "GM_DEPT_XL5";
```

我独立查看[after.png](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/out/objects/20261106_111613_013751/after.png)，它显示Step02该声明和原生语法错误“期望是statement (2,42)”。主控报告拆分后继续编译，才暴露下一项错误。没有在本agent运行编译器，故截图与主控操作链是现场证据，源码/语法核对是本agent静态判断，不冒充本agent重现。

最小处理是把赋值拆开（单独声明program再初始化也可以）：

```peoplecode
Local string &filename, &path, &program;
...
&program = "GM_DEPT_XL5";
```

不能扩大成“PeopleCode禁止Local初始化”。官方[Local语法参考](https://docs.oracle.com/cd/E24150_01/pt851h2/eng/psbooks/tpcl/htm/tpcl02.htm)明确给出 `Local Number &Constant = 42;`。本轮推荐分开声明/赋值，是为避开本次失败组合；该文档为8.51参考，不把它标成8.57实机编译结果。

### P1-2：单个SQL字符串字面量1006字符，越过当前编译器的1000字符限制

**这不是3985字符源码总长或4036 CRLF字节触发的4KB总量限制。** 本次根因有三条相互支持的证据：

1. 我读取失败MCP请求中的原始Step02文本，独立解析原稿第29行 `CreateSQL("...", ...)`：该SQL字面量内容为 **1006个字符**，全ASCII，所以不是中文字节/字符换算问题。上轮实际保存并已重建的XL4 SQL字面量为 **970字符**；新增临时表/进程过滤后越过1000，能够解释为什么近似旧代码能编译。
2. 我独立查看主控给出的第二张真实截图，实际本机路径为 [psauto/debug/on_error/2026.11.06-11.22.01.926_A1_Dirty.png](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/debug/on_error/2026.11.06-11.22.01.926_A1_Dirty.png)，显示原生 **“文本太长 (2,2)”**。图中源码仍是单个长CreateSQL字面量。原请求中的路径省略了psauto前缀，已按本机文件纠正。
3. 我于 **2026-11-06 11:25:39.366936 +08:00** 直接只读查询本机HRDEV消息目录，(2,2)的说明明确为：**“文本超过了允许的最大文本长度 (1000 个字符)。请将文本缩短，或将它截短成多个较短的文本，然后顺次连接起来。”** 这是当前部署库的消息证据，强于只引用网上不同版本的限值猜测；结合该8.57现场截图及1006字符原稿，足以确定此处超限。

字面量需拆成独立的短字符串再用 `|` 连接。仅在同一个引号内部插入换行，仍是同一字面量，不保证解决；也不应删字段、删实例条件来凑长度。多个短header字面量在一条1003字符长行里，不等同于“一个1003字符字符串”。Step01是SQL动作正文，也不是把整段INSERT SQL放到一个PeopleCode字面量，不能把这个限制误套到Step01并截短它。

### 对当前源码的最小处理建议及独立内存结果

主控已在我开始检查时修改了[当前源码第11行](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/demos/dept_export/temp_export_peoplecode.pcode:11)及[第30行](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/demos/dept_export/temp_export_peoplecode.pcode:30)：

```peoplecode
Local string &filename, &path, &program, &sqlText;
...
&program = "GM_DEPT_XL5";
...
&sqlText = "<第一段>" |
   "<第二段>" |
   "<第三段>";
&cursor = CreateSQL(&sqlText, &aet.PROCESS_INSTANCE.Value);
```

**独立静态/内存核对结果：** 三段分别为 **450/450/106字符**，拼接后与冻结失败请求的1006字符SQL **逐字符完全相等**。即使当前分界把FTE_EDIT_INDC和BJ_HRBP_ID拆在标识符中间，连接处没有额外空白，重建标识符仍正确。全部字符串字面量最大450字符；最长源代码行仍1003字符，是60个独立短header组成的行，不是一个超长字面量。当前源码为4042个LF字符/4097原始CRLF字节；不能把“超过4096字节”直接判成同一错误。

因此**当前三段方案已是可用的最小范围修订，无需为了此错误继续压缩整个程序、删注释或改60列表头**。如果只求最小文字diff，原单个CreateSQL字面量也可在逗号边界拆成两个642/364字符片段：

```peoplecode
&cursor = CreateSQL("SELECT SETID, DEPTID, TO_CHAR(EFFDT, 'YYYY-MM-DD'), EFF_STATUS, DESCR, DESCRSHORT, COMPANY, SETID_LOCATION, LOCATION, TAX_LOCATION_CD, MANAGER_ID, MANAGER_POSN, BUDGET_YR_END_DT, BUDGET_LVL, GL_EXPENSE, EEO4_FUNCTION, CAN_IND_SECTOR, ACCIDENT_INS, SI_ACCIDENT_NUM, HAZARD, ESTABID, RISKCD, GVT_DESCR40, GVT_SUB_AGENCY, GVT_PAR_LINE2, GVT_PAR_LINE3, GVT_PAR_LINE4, GVT_PAR_LINE5, GVT_PAR_DESCR2, GVT_PAR_DESCR3, GVT_PAR_DESCR4, GVT_PAR_DESCR5, FTE_EDIT_INDC, DEPT_TENURE_FLG, TL_DISTRIB_INFO, USE_BUDGETS, USE_ENCUMBRANCES, USE_DISTRIBUTION, BUDGET_DEPTID, HP_STATS_DEPT_CD, HP_STATS_DPCD_NW, HP_STATS_FACULTY, MANAGER_NAME, ACCOUNTING_OWNER, " |
   "COUNTRY_GRP, HP_RTBC_OPTION, HP_AUTO_RTBC, CLASS_UNIT_NZL, ORG_UNIT_AUS, WORK_SECTOR_AUS, APS_AGENT_CD_AUS, IND_COMMITTEE_BEL, NACE_CD_BEL, TO_CHAR(LASTUPDDTTM, 'YYYY-MM-DD HH24:MI:SS.FF6'), HPS_ROOT_NODE, HPS_DEPT_LVL, HPS_DEPT_BUD_NUM, HPS_ORG_STRUCTURE, BJ_HRBP_ID, BJ_DEPT_RESP FROM %Table(GM_DEPT_TMP) WHERE PROCESS_INSTANCE = :1 ORDER BY SETID, DEPTID, EFFDT", &aet.PROCESS_INSTANCE.Value);
```

上述示例在本agent内存中拼接验证为原SQL1006字符，未写入业务文件。没有用PeopleCode编译器执行该示例，不能保证它越过本次两项后不会遇到其他错误；实际编译与clipboard到达内容检查仍由主控完成。

当前ae_request.json的Step02 code与当前独立pcode在CRLF/LF规范化后相同，二者都不再含原多变量初始化组合或超过1000字符的SQL字面量。**最小修复应同时保持请求payload与pcode一致，不能只改本地文件而继续粘贴旧JSON。** 本次已检查二者一致，但未查看/读取实际业务剪贴板。

### 当前版本SHA及证据身份

旧SHA继续见初报。本次11:26左右工作区快照（原始字节SHA256）：

```text
1fc59282ad40320220c8ea37c55595ef262ec5fc66d9d6874c812b4adbf38864  record_request.json
3eb6ad2a7c0e905f5c85f621df7ea4fc9142da9cff699e01376f1b0cb5b5a61e  ae_request.json
c54185fadc58a1e434a8ab968fb621d233ab6731e4e46349690534b870f5a6c5  step01_insert.sql
ba1f968f03f8d9d3cf56deb22ea68d98965081fa172412303dc01c9dcdd5ea5f  temp_export_peoplecode.pcode
b020505f882ebc26f99ccd0dcf1f28ba1c47115e961608d6ea1ded886a0d8cd3  project_request.json
```

失败请求request.json SHA为 `f5c43ec3dfab1dd2b6729bb33a2f17732b4ef6a85be816b0ee1d0a9bb11c2ad5`。after.png SHA为 `185347bc20459587dc970c6abf90aa5e113ff6d17606a79fb514d84d6448aa7d`；第二张Dirty截图SHA为 `3138cc885e0eb6cda01759b9636db8c7f386ba9864a53eb0dbbc5aa5d1426807`。当前输入由主控编辑，非本agent修改，后续再变更需以新SHA为准。

本次唯一新增DB查询及原始返回：

```sql
SELECT SYSTIMESTAMP AS QUERY_TIME,MESSAGE_SET_NBR,MESSAGE_NBR,MESSAGE_TEXT,DESCRLONG FROM PSMSGCATDEFN WHERE MESSAGE_SET_NBR=2 AND MESSAGE_NBR IN (2,42) ORDER BY MESSAGE_NBR;
```

```text
| QUERY_TIME | MESSAGE_SET_NBR | MESSAGE_NBR | MESSAGE_TEXT | DESCRLONG |
|---|---|---|---|---|
| 2026-11-06T11:25:39.366936+08:00 | 2 | 2 | 文本太长。 | 文本超过了允许的最大文本长度 (1000 个字符)。

请将文本缩短，或将它截短成多个较短的文本，然后顺次连接起来。 |
| 2026-11-06T11:25:39.366936+08:00 | 2 | 42 | 语法错误: 期望是 %1。 | PeopleCode 程序的语法无效。PeopleCode 处理程序期望在出错位置找到指出的程序元素。

请检查 PeopleCode 程序并更正语法错误以遵守语言规范。 |
(2 rows, 42ms)
```

**附记结论：原稿两处编译阻断成立，初审漏检已更正；当前分开赋值＋450/450/106字符串拼接与原SQL等价，满足本次已定位的语法/字面量长度修订要求，但尚无本agent的实际编译或执行通过。** 既有P2文件有效性、Java/JVM和Excel验收边界不变。本次未改任何业务源码、未操作UI/剪贴板/数据库写入、未重跑旧Pipeline；只追加本报告。


## 已保存XL5/编译/Project的定向DBX确认 — 2026-11-06 03:35:39 UTC（UTC；北京时间加8小时）

主控提供新证据后，只对已保存XL5、关联临时表和Project作独立DBX SELECT，不重审Pipeline、不重跑完整测试、不操作浏览器或AE。数据库采样为 **2026-11-06 11:32:13.136901 +08:00至11:34:03左右**。当前五输入SHA仍为上段修复后快照（ae_request `3eb6ad2a...`、pcode `ba1f968f...`，其余三份原SHA未变）。早先“对象尚未创建”“尚无编译”的内容继续作为当时时间范围的历史，本段更新后续实际状态。

**两项P1在当前保存/编译版本关闭。** 这次是本agent直接查询实际DB源码和编译对象，而不是仅重复主控的结论：

- PSPCMTXT的完整对象键仍为 `66:GM_DEPT_XL5/77:MAIN/39:GBL/20:default/21:1900-01-01/78:Step02/12:OnExecute`，查询全部PROGSEQ仅一行0，`HASH_SIGNATURE=Kig86a1jH0UeeYHjB+teZ2uUWvMA`、CLOB **4048字符**。独立读取五个有界十六进制块，重建全文长度4048；UTF-8原文SHA-256为 **`ec7ca99e4262c205581f3d00438c2afec6a34e34f36488bcdafddc00361c1013`**，完整原文嵌入下方，未另写未经授权的源码文件。
- 独立对比DB原文与当前JSON的Step02和独立pcode：保留字符串内容的PeopleCode token序列完全相同，差异只有编辑器换行/缩进。DB中声明已与program赋值分离；SQL字面量仍是 **450/450/106**，拼接1006字符、最大单个字面量450。没有把DB自动排回一行误认为重新合成了一个1006字符字面量，三个引号片段及连接符都保留。
- PSPCMPROG对应同一Step02仅PROGSEQ=0，**PROGLEN=7369，LASTUPDDTTM=2026-11-06 11:23:37.202406**。结合已保存的修订源码及主控真实编译保存记录，足以关闭前述语法与字面量长度阻断；不是“仅凭编译长度推断Java可运行”。
- Step01/Step02为唯一两个active步骤，序号1/2，语句类型分别S/P。Step01实际SQLID=`GM_DEPT_XL5 MAIN    Step01  S`，PSSQLTEXTDEFN仅SEQNUM=0；其完整SQL经独立token对比，与当前ae_request Step01及step01_insert.sql一致，仅空白/分号格式差别。仍为61目标列、%ProcessInstance＋60源列的全量INSERT SELECT。

### 实际属性与校准临时表

独立DBX确认XL5的Disable Restart=Y、唯一默认状态GM_DEPT_AET/Y、临时表绑定GM_DEPT_TMP；TEMPTBLINSTANCES=0。后者是当前保存属性，不等于已经证明编号实例已分配或实际采用哪个物理表，运行时%Table解析/回退行为仍未验收。

GM_DEPT_TMP为RECTYPE=7、FIELDCOUNT=61；物理PS_GM_DEPT_TMP也61列，表空间HRAPP；唯一索引VALID，键顺序为PROCESS_INSTANCE/SETID/DEPTID/EFFDT（索引位于PSINDEX，不把表空间和索引表空间混淆）。按字段名比较，60个数据列的数据类型、字符长度和TIMESTAMP(6)精度没有窄化；特别是LASTUPDDTTM实际为TIMESTAMP(6)、BJ_DEPT_RESP为VARCHAR2(500)。**存在一项约束差别：源EFFDT为NOT NULL，临时EFFDT允许NULL**；不能声称60列所有NULL约束完全一致。当前业务从非NULL源值显式复制，不会因此制造NULL；也不能把该唯一索引扩大为对任意其他写入都强制非NULL主键的保证。

主控指出的顺序差异已由本agent对完整PSRECFIELD和USER_TAB_COLUMNS核实：

| 位置（含PROCESS_INSTANCE） | 请求顺序 | 定义和物理表实际顺序 |
|---|---|---|
| 33 | GVT_PAR_DESCR5 | FTE_EDIT_INDC |
| 34 | FTE_EDIT_INDC | GVT_PAR_DESCR5 |

其他59个位置相同，字段集合及四键无缺失。**校准对象不满足原请求的逐项字段顺序，不能称61字段顺序回归通过。** 但Step01显式列名清单决定值的对应关系，Step02显式投影决定Fetch顺序，header顺序与投影相同，因此这两个物理列互换**不会使当前这份业务SQL把值写到错误字段、或让导出列错配**；这是Oracle列名语义的静态结论，不是已执行导出。新GM_DEPT_QA的完整顺序回归由主控另记，本agent没有查询、等待或操作该对象。

### Project与主控新证据

独立查询GM_DEPT_TEXP的类型分组，总数 **822**：类型0=65、2=646、4=107、30=1、33=1、34=1、43=1。核心对象键实际包含GM_DEPT_TMP及其61字段、GM_DEPT_AET及其两字段、GM_DEPT_XL5、MAIN、**SQL类型30的Step01 SQLID、PeopleCode类型43的Step02 OnExecute**。这是本次直接DB查询支持的覆盖，不能把“822”理解为仅822段新业务代码或自包含运行依赖；未逐个审查全部822个关联定义正文，也未验证迁移目标。

另外读取主控归档，清楚区分来源：

- `out/runs/20261106_112341_779496/summary.json`：修订保存收尾11/11节点，0节点/动作失败，10.953秒原生跨度；这是主控运行的局部修订记录，并非新的整对象MCP，也不是执行AE。SHA `28be181b334439e41c3c1b35cf1e1096c4f532df23b61b3060af7388a87309a2`。
- `out/dept_tmp_ae_qa_result.json`：另一个 **AE GM_DEPT_QAE** 的完整创建返回saved_and_closed，state/restart/temp/properties标记、证据complete及允许下一操作均true。SHA `68fbe8d36a5dd377fcbd1c8bf8d1f9f65449e8277038115b2496caa70a220d76`。本agent只读此返回，未在本轮独立核验该QA AE的全部源码，不把它与正在校准的Record GM_DEPT_QA混淆。
- `out/dept_tmp_project_result.json`：GM_DEPT_TEXP完整保存关闭，definitions_added=3、evidence complete、next allowed；SHA `8f1fb7ac66f2f2033b51126f97bab089f10294df2a154ba281c6afc1639ed018`。Project成员总数822由上述本agent新DBX独立复查支持。
- 主控 `dept_ae_dbx.json` SHA `37434c9e276778cf34633f4f752295ee59ece81f91ca80b24dedad785d2924d3`；`dept_project_record_dbx.json` SHA `621b4ed2cbc55a6ea2cdaa4053f270c6b244bd3dc4abe214f128ebffdd3f0cae`。不以这两份旧查询取代上面的独立DB读取。

**当前结论：两个原稿P1已在上述明确DB源码/编译快照关闭；创建、绑定、Step01/Step02及Project核心覆盖已有DB证据。P2的FileExists/有效工作簿判决、JVM/Java方法、实际AE运行、完整数据/并发隔离和Excel输出验收均未关闭。** 无浏览器、编译、AE运行或写库由本agent执行；没有重写旧失败为成功，也没有等待GM_DEPT_QA。

### 本次从DB重建的完整Step02（UTF-8/LF，4048字符）

```peoplecode
/* Department export through a PeopleSoft Temporary Table.
   MAIN.Step02.OnExecute reads only this AE instance's rows. */
Declare Function buildJavaArray PeopleCode HPS_RPT_FUNC_WK.FUNCLIB_01 FieldFormula;

Local JavaObject &report;
Local SQL &cursor;
Local Record &aet;
Local array of any &headers, &row;
Local number &rows = 0;
Local number &col;
Local string &filename, &path, &program, &sqlText;

&program = "GM_DEPT_XL5";
&aet = GetRecord(Record.GM_DEPT_AET);
&filename = &program | "_" | DateTimeToLocalizedString(%Datetime, "yyyyMMdd_HHmmss") | "_" | String(&aet.PROCESS_INSTANCE.Value) | ".xlsx";
&aet.FILE_NAME.Value = &filename;
&path = %FilePath;
If None(&path) Or
      &path = Char(92) Then
   &path = GetEnv("PUBLIC") | Char(92) | "Documents" | Char(92);
End-If;
If Right(&path, 1) <> Char(92) And
      Right(&path, 1) <> "/" Then
   &path = &path | Char(92);
End-If;
&path = &path | &filename;
MessageBox(0, "", 0, 0, &program | " START; source=GM_DEPT_TMP; columns=60; path=" | &path);

&report = CreateJavaObject("hps.excel.poi.HpsReportDefn", "Department full export");
&headers = CreateArrayAny("SETID", "DEPTID", "EFFDT", "EFF_STATUS", "DESCR", "DESCRSHORT", "COMPANY", "SETID_LOCATION", "LOCATION", "TAX_LOCATION_CD", "MANAGER_ID", "MANAGER_POSN", "BUDGET_YR_END_DT", "BUDGET_LVL", "GL_EXPENSE", "EEO4_FUNCTION", "CAN_IND_SECTOR", "ACCIDENT_INS", "SI_ACCIDENT_NUM", "HAZARD", "ESTABID", "RISKCD", "GVT_DESCR40", "GVT_SUB_AGENCY", "GVT_PAR_LINE2", "GVT_PAR_LINE3", "GVT_PAR_LINE4", "GVT_PAR_LINE5", "GVT_PAR_DESCR2", "GVT_PAR_DESCR3", "GVT_PAR_DESCR4", "GVT_PAR_DESCR5", "FTE_EDIT_INDC", "DEPT_TENURE_FLG", "TL_DISTRIB_INFO", "USE_BUDGETS", "USE_ENCUMBRANCES", "USE_DISTRIBUTION", "BUDGET_DEPTID", "HP_STATS_DEPT_CD", "HP_STATS_DPCD_NW", "HP_STATS_FACULTY", "MANAGER_NAME", "ACCOUNTING_OWNER", "COUNTRY_GRP", "HP_RTBC_OPTION", "HP_AUTO_RTBC", "CLASS_UNIT_NZL", "ORG_UNIT_AUS", "WORK_SECTOR_AUS", "APS_AGENT_CD_AUS", "IND_COMMITTEE_BEL", "NACE_CD_BEL", "LASTUPDDTTM", "HPS_ROOT_NODE", "HPS_DEPT_LVL", "HPS_DEPT_BUD_NUM", "HPS_ORG_STRUCTURE", "BJ_HRBP_ID", "BJ_DEPT_RESP");
&report.addHeaderRow(buildJavaArray(&headers));
&sqlText = "SELECT SETID, DEPTID, TO_CHAR(EFFDT, 'YYYY-MM-DD'), EFF_STATUS, DESCR, DESCRSHORT, COMPANY, SETID_LOCATION, LOCATION, TAX_LOCATION_CD, MANAGER_ID, MANAGER_POSN, BUDGET_YR_END_DT, BUDGET_LVL, GL_EXPENSE, EEO4_FUNCTION, CAN_IND_SECTOR, ACCIDENT_INS, SI_ACCIDENT_NUM, HAZARD, ESTABID, RISKCD, GVT_DESCR40, GVT_SUB_AGENCY, GVT_PAR_LINE2, GVT_PAR_LINE3, GVT_PAR_LINE4, GVT_PAR_LINE5, GVT_PAR_DESCR2, GVT_PAR_DESCR3, GVT_PAR_DESCR4, GVT_PAR_DESCR5, FTE_EDI" | "T_INDC, DEPT_TENURE_FLG, TL_DISTRIB_INFO, USE_BUDGETS, USE_ENCUMBRANCES, USE_DISTRIBUTION, BUDGET_DEPTID, HP_STATS_DEPT_CD, HP_STATS_DPCD_NW, HP_STATS_FACULTY, MANAGER_NAME, ACCOUNTING_OWNER, COUNTRY_GRP, HP_RTBC_OPTION, HP_AUTO_RTBC, CLASS_UNIT_NZL, ORG_UNIT_AUS, WORK_SECTOR_AUS, APS_AGENT_CD_AUS, IND_COMMITTEE_BEL, NACE_CD_BEL, TO_CHAR(LASTUPDDTTM, 'YYYY-MM-DD HH24:MI:SS.FF6'), HPS_ROOT_NODE, HPS_DEPT_LVL, HPS_DEPT_BUD_NUM, HPS_ORG_STRUCTURE, B" | "J_HRBP_ID, BJ_DEPT_RESP FROM %Table(GM_DEPT_TMP) WHERE PROCESS_INSTANCE = :1 ORDER BY SETID, DEPTID, EFFDT";
&cursor = CreateSQL(&sqlText, &aet.PROCESS_INSTANCE.Value);
&row = CreateArrayAny();
While &cursor.Fetch(&row)
   If &row.Len <> 60 Then
      Error &program | " unexpected column count";
   End-If;
   For &col = 1 To &row.Len
      /* String[] preserves leading-zero identifiers and nulls as empty cells. */
      &row [&col] = &row [&col] | "";
   End-For;
   &report.addContentRowObject(buildJavaArray(&row));
   &rows = &rows + 1;
   If Mod(&rows, 10000) = 0 Then
      MessageBox(0, "", 0, 0, &program | " fetched " | String(&rows) | " rows");
   End-If;
End-While;
&cursor.Close();
&report.generateExcel(&path);
&report = Null;
If Not FileExists(&path, %FilePath_Absolute) Then
   Error &program | " workbook was not created: " | &path;
End-If;
MessageBox(0, "", 0, 0, &program | " COMPLETE; source=GM_DEPT_TMP; columns=60; rows=" | String(&rows) | "; path=" | &path);
```

### 本次独立只读SQL与时间

以下记录本次所有只读语句，结果摘要已在上文逐项给出；同一次查询中的元数据跨语句采样，不冒充一致性事务。完整源码由pc_hex查询重建并附上原文/长度/SHA，项目核对为总数及核心键，未伪称读遍822份正文。

**identity，2026-11-06 03:32:15 UTC**

```sql
SELECT SYSTIMESTAMP AS QUERY_TIME,SYS_CONTEXT('USERENV','CURRENT_SCHEMA') AS CURRENT_SCHEMA FROM DUAL;
```

**pc_identity，2026-11-06 03:32:15 UTC**

```sql
SELECT OBJECTID1,OBJECTVALUE1,OBJECTID2,OBJECTVALUE2,OBJECTID3,OBJECTVALUE3,OBJECTID4,OBJECTVALUE4,OBJECTID5,OBJECTVALUE5,OBJECTID6,OBJECTVALUE6,OBJECTID7,OBJECTVALUE7,PROGSEQ,HASH_SIGNATURE,DBMS_LOB.GETLENGTH(PCTEXT) AS SOURCE_CHARS FROM PSPCMTXT WHERE OBJECTID1=66 AND OBJECTVALUE1='GM_DEPT_XL5' ORDER BY OBJECTVALUE2,OBJECTVALUE6,PROGSEQ;
```

**pc_hex，2026-11-06 03:32:15 UTC**

```sql
SELECT P.PROGSEQ,N.N AS CHUNK,DBMS_LOB.GETLENGTH(P.PCTEXT) AS SOURCE_CHARS,RAWTOHEX(UTL_RAW.CAST_TO_RAW(DBMS_LOB.SUBSTR(P.PCTEXT,1000,1+1000*(N.N-1)))) AS SOURCE_HEX FROM PSPCMTXT P CROSS JOIN (SELECT LEVEL N FROM DUAL CONNECT BY LEVEL<=5) N WHERE P.OBJECTID1=66 AND P.OBJECTVALUE1='GM_DEPT_XL5' AND P.OBJECTVALUE6='Step02' ORDER BY P.PROGSEQ,N.N;
```

**compiled，2026-11-06 03:32:15 UTC**

```sql
SELECT OBJECTVALUE1,OBJECTVALUE2,OBJECTVALUE3,OBJECTVALUE4,OBJECTVALUE5,OBJECTVALUE6,PROGSEQ,PROGLEN,LASTUPDDTTM FROM PSPCMPROG WHERE OBJECTID1=66 AND OBJECTVALUE1='GM_DEPT_XL5' ORDER BY OBJECTVALUE6,PROGSEQ;
```

**properties，2026-11-06 03:32:15 UTC**

```sql
SELECT A.AE_APPLID,A.AE_DISABLE_RESTART,A.TEMPTBLINSTANCES,S.AE_STATE_RECNAME,S.AE_DEFAULT_STATE,A.LASTUPDDTTM FROM PSAEAPPLDEFN A LEFT JOIN PSAEAPPLSTATE S ON S.AE_APPLID=A.AE_APPLID WHERE A.AE_APPLID='GM_DEPT_XL5';
```

**bindings，2026-11-06 03:32:15 UTC**

```sql
SELECT AE_APPLID,RECNAME FROM PSAEAPPLTEMPTBL WHERE AE_APPLID='GM_DEPT_XL5' ORDER BY RECNAME;
```

**sql，2026-11-06 03:32:15 UTC**

```sql
SELECT S.AE_APPLID,S.AE_SECTION,S.AE_STEP,S.AE_STMT_TYPE,T.SQLID,T.SEQNUM,T.SQLTEXT FROM PSAESTMTDEFN S LEFT JOIN PSSQLTEXTDEFN T ON T.SQLID=S.SQLID WHERE S.AE_APPLID='GM_DEPT_XL5' ORDER BY S.AE_STEP,S.AE_STMT_TYPE,T.SEQNUM;
```

**project_counts，2026-11-06 03:32:15 UTC**

```sql
SELECT OBJECTTYPE,COUNT(*) AS MEMBERS FROM PSPROJECTITEM WHERE PROJECTNAME='GM_DEPT_TEXP' GROUP BY OBJECTTYPE ORDER BY OBJECTTYPE;
```

**project_core，2026-11-06 03:32:15 UTC**

```sql
SELECT OBJECTTYPE,OBJECTID1,OBJECTVALUE1,OBJECTID2,OBJECTVALUE2,OBJECTID3,OBJECTVALUE3,OBJECTID4,OBJECTVALUE4 FROM PSPROJECTITEM WHERE PROJECTNAME='GM_DEPT_TEXP' AND (OBJECTTYPE IN (30,33,34,43) OR (OBJECTTYPE=0 AND OBJECTVALUE1 IN ('GM_DEPT_TMP','GM_DEPT_AET'))) ORDER BY OBJECTTYPE,OBJECTVALUE1,OBJECTVALUE2,OBJECTVALUE3;
```

**record_fields，2026-11-06 03:32:15 UTC**

```sql
SELECT D.RECNAME,D.RECTYPE,D.FIELDCOUNT,R.FIELDNUM,R.FIELDNAME,CASE WHEN BITAND(R.USEEDIT,1)=1 THEN 'Y' ELSE 'N' END AS KEY_FLAG FROM PSRECDEFN D JOIN PSRECFIELD R ON R.RECNAME=D.RECNAME WHERE D.RECNAME='GM_DEPT_TMP' ORDER BY R.FIELDNUM;
```

**physical_columns，2026-11-06 03:32:15 UTC**

```sql
SELECT TABLE_NAME,COLUMN_ID,COLUMN_NAME,DATA_TYPE,CHAR_LENGTH,DATA_SCALE,NULLABLE FROM USER_TAB_COLUMNS WHERE TABLE_NAME IN ('PS_GM_DEPT_TMP','PS_DEPT_TBL') ORDER BY TABLE_NAME,COLUMN_ID;
```

**physical_keys，2026-11-06 03:32:15 UTC**

```sql
SELECT I.TABLE_NAME,I.TABLESPACE_NAME,I.INDEX_NAME,I.UNIQUENESS,I.STATUS,C.COLUMN_POSITION,C.COLUMN_NAME FROM USER_INDEXES I JOIN USER_IND_COLUMNS C ON C.INDEX_NAME=I.INDEX_NAME AND C.TABLE_NAME=I.TABLE_NAME WHERE I.TABLE_NAME='PS_GM_DEPT_TMP' ORDER BY I.INDEX_NAME,C.COLUMN_POSITION;
```

**final_table，2026-11-06 03:34:03 UTC**

```sql
SELECT TABLE_NAME,TABLESPACE_NAME FROM USER_TABLES WHERE TABLE_NAME='PS_GM_DEPT_TMP';
```

**final_steps，2026-11-06 03:34:03 UTC**

```sql
SELECT AE_APPLID,AE_SECTION,AE_STEP,AE_SEQ_NUM,AE_ACTIVE_STATUS FROM PSAESTEPDEFN WHERE AE_APPLID='GM_DEPT_XL5' ORDER BY AE_SEQ_NUM;
```
