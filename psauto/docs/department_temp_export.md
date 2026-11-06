# 部门导出临时表方案

部门导出现在可以由同一套 MCP 组合成两个对象：`GM_DEPT_TMP`（Temporary Table）和 `GM_DEPT_XL5`（AE）。临时表包含 `PROCESS_INSTANCE` 以及 `PS_DEPT_TBL` 的全部 60 个物理列，共 61 个字段；`PROCESS_INSTANCE`、`SETID`、`DEPTID`、`EFFDT` 为键，供运行时按进程号隔离数据。

AE 的两个步骤固定为：

1. Step01 SQL：`INSERT INTO %Table(GM_DEPT_TMP) (...) SELECT %ProcessInstance, ... FROM PS_DEPT_TBL`。
2. Step02 PeopleCode：按 AET 中的 `PROCESS_INSTANCE` 查询 `%Table(GM_DEPT_TMP)`，复用现有 `HpsReportDefn`/`buildJavaArray` 组件生成 `.xlsx`。

接口仍使用通用 `create_record`、`create_ae` 和 `save_project`，没有新增业务专用的浏览器操作。`create_record` 的字段上限已扩为 61，MCP schema 和内部参数模型一致。

大 Record 创建先用原生窗口按钮固定最大化状态，再插入字段。唯一匹配时用结果行的蓝色状态判断已自动插入；多结果时精确选中目标再插入。关闭对话框后，聚焦网格、移动到末行，在 22×15 像素的数字单元格中识别预期行号，并点击该行，确保下一字段按顺序追加。输入框仍使用完整名称规则，`EEO4_FUNCTION` 的 O/0 问题通过收窄原图 ROI 解决，不把数字0放宽成字母O。字段内容和顺序交给 DBX 最终验收。

字段插入结束后恢复普通 Record 窗口。四个键的属性仍由原始 MR3A `NodeOverride` 组件绑定；设置前先回到首行并定位目标，随后继续原有类型、保存、Build 和关闭流程。每步的识别、动作、延迟及失败都记录在 Maa 原生日志中，不自动重放失败的创建。

可复用请求和 PeopleCode 位于 [dept_export demo](../demos/dept_export/README.md)。MCP 创建的是新对象 `GM_DEPT_XL5`，因为当前接口对已存在对象只做查重并释放工作台，不提供覆盖保存；已有 `GM_DEPT_XL4` 会保留。

创建结果以 Pipeline 的保存、关闭、Build、临时表绑定终态和 DBX 元数据为准。实际 Process Scheduler/JVM 运行及 `.xlsx` 内容仍需 PeopleTools 的 Java 报表运行依赖，不能用对象创建成功替代运行验收。

pshelp 已完成本轮五份业务输入及实际保存对象的[独立只读审核](pshelp_department_temp_review_20261106.md)。报告保留创建过程中的快照、两处编译阻断及后续修复确认，各段按其时间和SHA读取。`FileExists` 只确认文件存在，无法替代真实 `.xlsx` 格式、内容和大行数验收，该 P2 留在运行验收范围。

实际编译发现并修复了原稿的两处 P1：多变量 `Local` 声明中的初始化组合，以及1006字符的单个SQL字面量。前者拆成声明和赋值，后者按450/450/106字符连接，重组SQL逐字不变。pshelp 在11:35追加独立DBX确认：XL5实际Step02源码4048字符、编译长度7369，保存源码与当前payload的token一致，两项P1在该版本关闭。初审、编译失败和后续修复的时间范围均保留在报告中。

`GM_DEPT_TMP` 是分段校准对象，字段33/34物理顺序与请求互换；业务SQL显式指定列名，所以数据映射不依赖这两列的物理顺序。其60个业务列的类型、长度及时间精度与源表一致，但 `EFFDT` 允许NULL而源表不允许。四键为PeopleSoft Key属性和VALID唯一索引，不能扩展理解为所有列的NOT NULL约束相同。当前全量INSERT来自源表非NULL的EFFDT，实际并发/实例分配和Excel运行仍另行验收。

最终用同一套通用MCP从头创建 `GM_DEPT_QA`＋Build，返回 saved_and_closed、built、workspace_ready、evidence complete、next allowed 均为true。DBX逐项确认其61字段定义与物理列顺序完全等于请求，四键和唯一索引正确。原生889节点全部完成，632.828秒、28次额外扫描、62次候选未命中、0节点/动作失败；候选未命中包含正常分支，不等于失败。证据导出另109.563秒，这些阶段不重复相加，不把本次不同字段规模当成旧五字段样本的性能对照。

两步AE的从头回归 `GM_DEPT_QAE` 也完整通过：108节点、89.516秒、默认AET/临时表/Restart/保存关闭终态齐全；DBX编译长度同为7369。业务Project `GM_DEPT_TEXP` 的完整MCP为72节点、54.453秒，DBX确认822个成员，含Step01 SQL与Step02 PeopleCode。完整调用与分段校准分别记录在[本轮证据](images/acceptance-dept-temp-20261106/README.md)，未改计历史失败。

本次普通套件148项，68通过、80按环境跳过；新增4项原生图像测试覆盖蓝色自动插入状态、O/0输入、1–11/1–25共36个真实数字单元格以及滚动后的第61行，均通过。既有原生视觉回归14项通过。以上均不表示AE已执行或Excel已生成。
