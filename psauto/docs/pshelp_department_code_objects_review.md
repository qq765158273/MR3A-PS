# PeopleSoft 部门导出业务代码与对象审核

轮次 `dept-export-code-objects-8878617-20261105`；完成时间 2026-11-06 00:32:07 +08:00（Asia/Shanghai）。仓库 `C:/Users/t-wangsen05/Desktop/MR3A-PS`，origin `https://github.com/qq765158273/MR3A-PS`，分支 `feat/psauto-jumpserver`，基线 `8878617eae57c12f1bca7e41a01d7f8ea4561c98`。目标为HRDEV的 `GM_DEPT_EXPORT` / 对照 `GMPRJFIX01`、`GM_DEPT_XL4.MAIN.Step01.OnExecute`、默认AET `GM_DEPT_AET` 及两个字段。

**结论：实际保存的60列SQL、表头顺序、AE/AET绑定和两个Project成员一致性有本agent独立DBX只读核验支持；实际生成可打开的大行数Excel仍未验收。确定发现是最终AE日志误标旧对象名（P3），以及业务层缺少输出文件完成/异常收尾协议的保护缺口（P2，文件后果取决于Java实现及故障）。没有证据确认列错位、错误状态绑定、实际截行或内存溢出。**

本次仅调用DBX `ps-dev` 的SELECT/describe，并做本地源码/归档截图和内存解析；没有运行AE、操作业务浏览器、DDL/DML、创建/修改PS对象、修改源码或提交。没有启动其他agent。只写本报告与同前缀证据目录。128项普通/6项Project测试属于前轮自动化验证，本轮未重跑，也不将它们计作业务代码正确性证明。工作区中主控正在另行扩展的Record接口/图片/Pipeline不属于本轮业务对象审核。

## 来源与可重复方法

**数据库源码是审核依据。** 从 `PSPCMTXT` 查询目标全部对象键和全部 `PROGSEQ`；实际仅有 `PROGSEQ=0`，CLOB为3937字符。再按1000字符分块，通过十六进制无损读取并重建 [GM_DEPT_XL4_MAIN_Step01_db.pcode](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/out/pshelp_department_code_objects_evidence/GM_DEPT_XL4_MAIN_Step01_db.pcode)。长度核对通过，SHA-256为 `a8ce701fda03283564e554ddd2e169c054fbb9c0459652eeb4dc01b14ac95e77`。完整键为 `66:GM_DEPT_XL4 / 77:MAIN / 39:GBL / 20:default / 21:1900-01-01 / 78:Step01 / 12:OnExecute`，DB `HASH_SIGNATURE=LgoiuIvrgOPOLaBYPIzuDIUZ/qkA`。

同法读取实际引用的 [HPS_RPT_FUNC_WK_FUNCLIB_01_db.pcode](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/out/pshelp_department_code_objects_evidence/HPS_RPT_FUNC_WK_FUNCLIB_01_db.pcode)：全部PROGSEQ为0，5099字符/5419 UTF-8字节，SHA-256 `8c30275ae0db65b04553e039cf3e79845e6686804abd409f9dd26501a8c78272`。还直接读取了既有 `BJ_CITY_RATE` 的相关PeopleCode，作为调用范例，未运行它。

本地未提交草稿为3925字符，原始工作区字节SHA为 `948783d43a6f3dfa7f1699c70b34eaf1433c75c2facdb46ab1836ee7fda2832e`；独立diff确认与DB源码只有两处 `Or/And` 条件换行缩进差异。**没有靠草稿代替DB核验，也没有把长度差说成业务代码不同。** 下文代码行号一律指重建的DB源码，不指草稿。

原始DBX返回、完整只读SQL及UTC采集时间保存在 [证据目录](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/out/pshelp_department_code_objects_evidence/README.md) 的各JSON中；源码长度/哈希见 `source_manifest.json`，三方列映射见 `column_mapping.json`，独立解析结果见 `independent_analysis.json`，本地输入文件SHA见 `local_input_sha256.json`。DBX显示连接名ps-dev、服务HRDEV；实际 `SESSION_USER/CURRENT_SCHEMA=SYSADM`，Oracle `DB_NAME=CDBHCM`，不把容器名与连接服务名混为一谈。这些是多次只读采样，并非冻结数据的一致性事务。

## 独立核验支持的内容

### 1. SQL覆盖当前全部60物理列及全部历史

从实际DB源码第31行提取60个表头，第33行提取SELECT投影，解析时保留函数括号内逗号，再与 `USER_TAB_COLUMNS ORDER BY COLUMN_ID` 比较：**三者均60列，名称/顺序逐项相同，无缺列、重复或错位**。规范化列序列SHA为 `e1db8accffa2e7e54fe9ee5f34ca55266986f8584d702d247f3d1047a742d6b8`。另将实际源码中的SQL包为只返回1行的SELECT在HRDEV执行，60列正确返回，含中文与 `2020-05-19 16:36:55.000000` 日期时间文本；这是Oracle投影验证，不能当作PeopleCode Fetch或Java写Excel的执行验证。

当前表类型为55个VARCHAR2、3个NUMBER、1个DATE、1个TIMESTAMP(6)。57项PeopleSoft记录字段通过三个子记录展开为60物理列，不能把 `PSRECFIELD` 的57行当作物理列数。SQL没有有效状态、当前日期、SETID或其他WHERE过滤，按SETID/DEPTID/EFFDT排序，包含有效和无效状态的历史行，符合本轮明确的“全部生效历史”范围。

独立COUNT快照为 **74762行、15692个SETID/DEPTID组合**，EFFDT从1900-01-01至2023-08-02，A状态60336行、I状态14426行。另查 `(SETID,DEPTID,EFFDT)` 重复组为0。这些是采集时事实，不是未来常量。没有执行74762行PeopleCode/Java导出。

EFFDT是DATE，当前非午夜值为0；`TO_CHAR(EFFDT,'YYYY-MM-DD')`适合有效日期语义，若将来物理DATE写入时分秒则该格式会舍去时间，不能宣称无条件保留任意Oracle DATE的全部信息。LASTUPDDTTM为TIMESTAMP(6)，源码显式格式化 `YYYY-MM-DD HH24:MI:SS.FF6`，SQL层保留6位小数；没有时区列可导出。两个允许NULL的列LASTUPDDTTM/BJ_DEPT_RESP在当前快照都没有NULL，不能把这次数据当作空值运行测试。

### 2. 声明/Fetch和数组接口静态一致，Java写入仍待验证

第9行使用 `array of any`，第34—35行空数组交给 `SQL.Fetch`，每行检查长度60；不是把60列绑定给一个标量。第39—43行先转字符串，再交给实际helper的 `buildJavaArray`。该helper在[第159行](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/out/pshelp_department_code_objects_evidence/HPS_RPT_FUNC_WK_FUNCLIB_01_db.pcode:159)接受array of any，分配 `java.lang.String[]` 并逐项反射赋值；传参与声明没有发现静态矛盾。

参考BJ_CITY_RATE用同一header helper，而正文用 `buildJavaArrayObject`（Object[]，其中含数值推断逻辑）。本AE选择String[]并非自动的类型错误：Java的String[]可赋给Object[]；但PeopleCode桥接/实际重载、Java内部如何写单元格仍须按部署类验证。仅凭范例调用、方法同名或PeopleCode编译长度，不能认定此次方法调用一定正确。

字符值先按字符串传递，避免在helper里被 `Value()` 主动转数值，方向上有利于保留前导零。三个Oracle NUMBER也会转成文本；用户本轮没有明确要求数值单元格，**不能单凭全文本策略定为代码缺陷**。需约定数值排序/计算、NULL与空白/空字符串的映射，再检查实际单元格类型。当前未对PeopleCode的NULL转换、数值零、中文、零前缀写Excel做运行测试。

### 3. AE/AET实际元数据符合代码引用

- `GM_DEPT_XL4`：非Library，普通AE；唯一active MAIN/Step01，唯一语句类型P；编译长度7264、编译元数据时间2026-11-05 21:37:25.555884。
- `AE_DISABLE_RESTART=Y`；唯一状态记录 `GM_DEPT_AET` 且 `AE_DEFAULT_STATE=Y`。禁用Restart符合本程序写外部文件的选择，但不自动提供重复运行幂等或文件清理。
- `GM_DEPT_AET`：RECTYPE=2（Derived/Work）、2字段。第一个PROCESS_INSTANCE为Number、10位、0小数；FILE_NAME为Character、80字符。不是需要Build的SQL状态表。代码用 `GetRecord(Record.GM_DEPT_AET)`，未再引用无效的%ProcessInstance。
- 当前命名模式 `GM_DEPT_yyyyMMdd_HHmmss_<10位实例号>.xlsx` 最长39字符，低于FILE_NAME的80字符；没有发现该字段长度导致当前文件名截断的问题。完整目录路径是另一项环境条件。
- `PSAEAPPLTEMPTBL`对最终AE没有记录。本业务源码也没有使用临时表，因此没有遗漏本程序所需临时表绑定的证据。

这些确认创建/编译/属性正确；不表示该对象已成功执行。

### 4. Project覆盖新定义，不能视作自包含运行包

本agent直接查询两个Project，各10行，去掉PROJECTNAME后成员的全部对象键逐项相同。含AET Record及两个Record Field成员、两个Field及标签、AE、MAIN、Step01 OnExecute。原GM_DEPT_EXPORT时间戳仍为 `2026-11-05T22:23:16.17893`。

实际代码所用 `HPS_RPT_FUNC_WK.FUNCLIB_01.FieldFormula` **不在这10项里**，`DEPT_TBL`和Java/JAR也不在其中。HRDEV里helper和数据表已存在，所以这不是当前库中已证实的缺失对象错误；但Project只覆盖本次新业务定义及其原生关联，不能宣称它独立携带所有执行依赖。跨环境迁移需列出既有helper、表/自定义列和HPS/POI JAR前置条件；不能仅按“10成员相同”证明可部署、可运行。Project本身也不冻结以后修改的源码。

## 确定发现及条件

### P2：业务层未建立生成文件的完成/异常收尾协议（静态保护缺口）

位置：[DB源码第17行](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/out/pshelp_department_code_objects_evidence/GM_DEPT_XL4_MAIN_Step01_db.pcode:17)、[第49行](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/out/pshelp_department_code_objects_evidence/GM_DEPT_XL4_MAIN_Step01_db.pcode:49)、[第50行](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/out/pshelp_department_code_objects_evidence/GM_DEPT_XL4_MAIN_Step01_db.pcode:50)。

FILE_NAME在生成前写入内存AET；程序对最终路径直接调用generateExcel，之后即报COMPLETE。源码无临时输出名→成功发布、生成后文件检查、自有catch清理或失败上下文记录分支。**若Java实现直接写最终文件，并在写入部分数据后抛异常/被中断，业务层没有删除或隔离该半成品的路径；若Java静默返回但未生成有效文件，业务层仍会发COMPLETE。** 这些是具体触发条件和源码保护缺口；Java是否内部采用原子发布、校验和异常清理尚未知，未制造真实故障，未观察到半成品，也不声称已运行复现。

不把缺少catch推断为SQL句柄必然泄漏，或AE一定吞错。PeopleCode未捕获异常可使AE失败并由进程收尾；Derived/Work FILE_NAME也是内存状态，不能宣称它会持久化污染数据库。正常路径确实先Close SQL再生成文件；改进应针对文件发布、实际日志和必要的对象释放，而非把空置Java变量当成已知资源泄漏。

建议：核实组件自身文件契约后，按需要在业务层补临时文件和成功发布、生成后可读性/结构检查、失败上下文及半成品处置；仅将成功生成的文件名作为“完成”结果。此建议不授权本轮改代码或运行故障注入。

### P3：最终XL4日志仍标旧GM_DEPT_XLSX，容易混淆本轮样本

位置：[第28行](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/out/pshelp_department_code_objects_evidence/GM_DEPT_XL4_MAIN_Step01_db.pcode:28)、第37/46/52行。START、列数错误、每万行进度和COMPLETE均硬编码旧 `GM_DEPT_XLSX`。对象实际为GM_DEPT_XL4，静态可确定；任何执行到对应语句都会产生旧标签，复现不需要先生成Excel。截图中早期程序自身也用该名字，更容易误归因。应改为实际程序/实例标识，并将实例、路径、行数放入同一条完成/失败记录。该问题不等于旧JVM日志来自XL4。

## 待验证风险及改进空间（不冒充已确认故障）

1. **实际格式/行数能力是验收阻断项。** 仓库范围未找到class/JAR，也没有最终工作簿。缺少HpsReportDefn实际构造器/方法签名、HSSF/XSSF/SXSSF及写出实现证据。扩展名“.xlsx”、既有示例和7264编译长度均不能证明OOXML或超过xls限制后的正确性。74762行数据加表头为74763行，已超过xls的65536行限制；xlsx单sheet也有1048576行上限，未来超过后需分sheet或明确拒绝，不能把当前样本推广为无限行数。
2. **内存与速度。** 源码只证明逐行Fetch、逐行向report添加，最后generateExcel；不证明Java内部保留全部行，也不证明它在流式写。不能据此断言当前必然OOM。当前量是4485720个正文单元格；helper每行GetJavaClass/CreateJavaArray、每格反射set，另有每格字符串拼接，总调用量可由源码推得，可能比SQL更费时。没有运行证据，不能给出秒数/峰值或把网络因素当根因。优先检查实际JAR和运行剖析，再决定使用现有组件的批量/流式能力，不宜先改共享helper影响其他报表。
3. **输出目录。** 第18—27行优先用%FilePath，空或单反斜杠时退回PUBLIC/Documents；只规范末尾分隔符，没有验证PUBLIC有效、目录可写/存在、磁盘空间或完整路径长度。若运行环境无有效PUBLIC且%FilePath空，会拼到根目录下Documents。目录错误应由运行前校验和错误日志明确，当前不能宣称最终XL4已选到可写目录；也没有证据说当前实际目录一定错误。
4. **精度和空值。** SQL日期/时间格式已有明确依据；PeopleCode到String[]再到Excel的NULL、空白、三种NUMBER、Unicode、前导零和公式样文本写出均未实测。没有看到主动执行公式的源码，不凭未知Java实现推断公式注入或数据变形。应先约定映射，再用小型边界样本和实际文件验收。
5. **计数和完成消息。** &rows计成功调用追加的行数，并非文件重新打开后计出的行数。文件验收应与本次SQL快照/一致性口径匹配；并发数据变化时，分开执行COUNT不天然等于导出时快照，不建议硬编码74762来“验收”。

## 环境证据与最终AE执行的边界

已独立查看归档 [ae_runtime_jvm_error.png](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/docs/images/acceptance-ae-properties-20261105/ae_runtime_jvm_error.png)：PeopleTools8.57.11，**GM_DEPT_XLSX，实例397097**，启动Java虚拟机错误(2,766)，原生步骤异常终止RC=8。它证明那次早期运行未成功；不能替代GM_DEPT_XL4运行日志。最终AE尚无成功执行/输出文件证据，本轮没有运行它。

64位PSIDE、客户端未找到配套JVM和旧Oracle目录JVM的结论来自主控先前诊断文档，本agent未操作远端去重新检查或尝试加载；也不能仅因JVM无法启动就精确断言必然是“未安装Java”，位数、版本、加载路径、依赖仍需诊断。PSIDE直接Run是用户优先路径，Process Scheduler是可选方案，PIA不可达不等于所有执行路径不可用。本轮未安装Java、改ACL或环境变量。

## 新接口需求的当前状态

| 能力 | 基线8878617 | 本轮观察/限制 |
|---|---|---|
| Disable Restart | 已有严格bool/可省略参数 | 最终AE实际Y；本轮未重测UI两态 |
| 一个默认state_record | 已支持 | 最终AE默认GM_DEPT_AET/Y |
| AE临时表列表绑定 | 无参数 | 最终AE临时表元数据为空；不作为新能力验收 |
| SQL Table、Derived/Work | 已支持 | 属既有接口 |
| SQL View、Dynamic View、Temporary Table | 基线未支持 | 当前工作区已出现RecordKind/view_sql等未提交扩展；只记录接口静态出现，未审其新对象/执行正确性 |

基线模型和MCP入口的Git字节快照保存在 `baseline_interfaces.json`。主控另行扩展的工作区文件可能继续变化，本轮没有把它们冻结、修改或列为已验收。

## 建议顺序及未完成项

1. 先只读取得拟在PSIDE加载的匹配64位JVM、HPS/POI JAR的实际版本/哈希/方法与工作簿实现；这能确定String[]桥接、OOXML和内存策略，不能用安装任意旧JVM试错。
2. 补文件完成/错误日志和必要的失败处置，修正旧对象名；明确文本/数值/NULL契约及目录。
3. 由主控在获运行授权后执行最终GM_DEPT_XL4。保留原生RC/实例、运行时计数及快照口径、实际输出文件，验证ZIP/OOXML可打开、60列、超过65536行、实际行数与完整历史、中文、零前缀/空值/6位小数，并记录峰值内存与耗时。**本轮不执行这一步。**
4. 若要迁移，明确依赖于已有表/自定义列/helper/JAR的环境清单；再验收新Record类型和AE临时表绑定，保持与本轮业务对象分开。

未完成项包括最终AE成功运行及全部文件验收、Java实现/签名/资源释放、异常/磁盘满/中断、长期与更大行数、新增接口实际对象测试。当前可确认“对象和投影基本符合设计”，不能确认“部门Excel业务已完成”。
