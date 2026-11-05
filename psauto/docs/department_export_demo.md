# 部门导出 AE demo 与自动开发验证

2026-11-05，需求是通过自动化开发 AE，导出 `PS_DEPT_TBL` 的全部列及全部生效历史行到 Excel，并观察自动化和 AE 的原生日志。

**目前完成了自动创建、默认 AET、Disable Restart、PeopleCode 编译和保存关闭的验收；实际 Excel 导出尚未通过。** App Designer 本地执行进入 PeopleCode 后报“无法启动 Java 虚拟机（2,766）”，AE 以 RC=8 终止。没有用创建成功或一份 Python 生成的 Excel 替代 AE 执行验收。

## 数据与实现

DBX 只读确认该表有 60 个物理列、当时 74,762 行。`PSRECFIELD` 有子记录定义，不能把其 57 行直接当作物理列数；demo 按物理列清单选择全部 60 列，不过滤当前日期或有效状态。EFFDT 和 LASTUPDDTTM 显式格式化，后者保留 6 位小数。

参考了 HRDEV 已有的 `BJ_CITY_RATE` 等报表 AE：它们使用 `hps.excel.poi.HpsReportDefn`、`HPS_RPT_FUNC_WK.FUNCLIB_01` 的数组辅助函数和 `generateExcel`。demo 同样复用现有组件，目标为真正的 `.xlsx`，不将 TSV/CSV 改扩展名冒充 Excel。选择 `.xlsx` 也避免 74,762 行超过旧式 `.xls` 单表上限。

`GM_DEPT_AET` 是 Derived/Work，包含 PROCESS_INSTANCE、FILE_NAME；与现有报表的内存 AET 模式一致，不需要 Build 物理表。代码通过 GetRecord 取得绑定 AET 的过程实例，文件名带时间和实例号，每 10,000 行记录进度。导出涉及外部文件操作，因此明确禁用 Restart。

业务 PeopleCode 仍是未完成运行验收的工作区草稿，位于 `psauto/demos/dept_export/`，本轮不提交它。当前能力的可信提交范围是已验证的 MCP 属性扩展、Pipeline、图片、测试和证据。

## 新增 MCP 参数

`create_ae` 增加两个可选参数：

| 参数 | 含义 |
| --- | --- |
| state_record | 已存在的 Record，新增为唯一默认 AET；应先创建该 Record |
| disable_restart | 严格布尔值；true 勾选 Disable Restart，false 清除，省略保持默认 |

示例元数据：

```json
{
  "name": "GM_DEPT_XL4",
  "state_record": "GM_DEPT_AET",
  "disable_restart": true,
  "steps": [{"type": "PeopleCode", "code": "<由调用方传入的代码>"}]
}
```

状态配置插在初次命名保存之后、粘贴 PeopleCode 之前，以支持代码引用 AET。所有界面步骤和分支仍在 `create_ae.json`，Python 仅绑定参数、串行执行及读取原生终态。创建工具依旧只保存关闭，不自动执行 AE。

状态记录只接受空列表或首行已经是所需默认 AET；不同的现有状态列表不被覆盖。动态 AET 名严格检查在与默认勾选同一首行。复选框按当前态分支，最多切换一次，之后必须识别目标态；没有重复切换。Add 还检查启用字形颜色，避免灰色按钮图片相似但不可用的情况。

对象身份在活动标题中、进入 Properties 前核验。Properties 固定标题用局部图片识别，避免对灰色后台标题再做容易漏下划线的 OCR。属性保存后仍验证活动对象和保存反馈。传入参数时，业务成功额外要求 StateBound、RestartVerified、PropertiesSaved 对应的原生终态；缺标记不能只凭保存关闭报告参数配置成功。

已有 MCP 服务进程不会热加载 Python 模块。这轮旧连接曾在任何业务动作前报 Config 缺少 canvas_refresh_mode；新参数和下面的验收使用新启动的同配置 stdio MCP 实例。更新代码后需要重新连接 MCP。

## 已验证范围

`GM_DEPT_AET` 完整创建 50.42 秒。最终 `GM_DEPT_XL4` 在身份和空列表保护修复后，通过新参数从头创建 66.50 秒，75 节点全部完成，0 节点失败、0 动作失败，3 次等待扫描、7 次候选未命中，证据 complete、允许下一操作。DBX 确认 GM_DEPT_XL4 默认状态为 GM_DEPT_AET/Y、Disable Restart=Y、Step01 PeopleCode 编译长度 7264。

修复前完整样本 GM_DEPT_XL3 用时 64.83 秒，其数据库中的 PeopleCode 包含与草稿一致的完整 60 列查询，绑定 AET 与报表类均存在；无效 `%ProcessInstance` 已移除。首次开发错误改为从 AET.PROCESS_INSTANCE 取值后才编译成功。XL3 与 XL4 的代码摘要相同；XL4 的 DBX 验收范围是默认 AET、Restart 及编译长度，未重复查询代码正文。`GM_DEPT_XLSX` 属于早先分段修复样本；`GM_DEPT_XL2` 是中间属性校准对象，不计完整创建通过。

最终普通套件 121 项中 55 通过、66 项按集成开关跳过；原生属性识别 6 项通过，覆盖占用列表、错误名称/默认行、布尔两态、点击未生效停止、真实标题的前缀对象名和完整空列表候选分支；原有 14 项原生视觉回归也通过。不同批次有重叠，不能累加成整体成功率。

pshelp 首次独立审核发现 P2：属性入口/保存的名称匹配接受前缀对象，以及 P3：只检查首行白色不能证明整个状态列表为空。修复为独立的完整标题对象段正则，以及整个 Selected 列表内部全白判决。pshelp 定向独立 native 复跑 2/2 通过，两项关闭；主控已全文读取最终附记并核对 24 个目标文件 SHA。完整历史和验证边界见 [独立审核报告](pshelp_ae_properties_review.md)。

最终原生事件跨度 54.938 秒：扫描准备 12.687 秒、识别 12.657 秒、动作前 0.046 秒、动作 16.189 秒、动作后等待 13.234 秒、未归属 0.125 秒；这些相加等于事件跨度。扫描准备包含截图、扫描间隔和其他准备，不能全部称为截图耗时。MCP 总时长另含约 10.104 秒证据导出及启动开销，不重复相加。当前单样本没有高失败率或无界重试证据；动作和等待比单次取图更值得后续按节点优化，不在未验证时盲减延迟。

最慢的四个节点分别为 AEProp_PasteState（3.000 秒）、A0_Paste（2.547 秒）、查重名称输入（2.484 秒）、首次命名输入（2.375 秒），均只有一次扫描、无候选未命中；主要涉及剪贴板与输入等待。3 次额外扫描分别在查重对话框、Definition Properties 和 Properties Ready。后续优化应针对这些实际耗时，保持目标状态检查，不能把候选分支未命中作为无条件重放输入的理由。

截图、逐节点 CSV、MCP 返回、分项及 DBX 返回见 [属性验收证据](images/acceptance-ae-properties-20261105/README.md)。

## 实际执行发现的问题

| 问题 | 证据与处理 |
| --- | --- |
| DESCR254 插入结果行识别为 DESCB254 | 首个三字段 SQL Table 试验停止在 R_Field2_Insert 之后，严格检查没有误选；未保存草稿已丢弃。最终 AET 根据现有报表采用 Derived/Work 两字段；该通用字段识别缺口未冒充已修复 |
| 无效系统变量 %ProcessInstance | 编译错误反馈阻止继续，首次 MCP 返回 partial；改从绑定 AET 取值后才得到编译结果 |
| Properties 后台灰标题丢下划线 | 去掉重复的后台名称 OCR，在进入前的活动对象身份检查和固定 Properties 图片之间按顺序执行；最终完整 MCP 已通过 |
| Run Request 日志文件名最多 30 字符 | 长路径被截成 Public/Documents/GM_D，按原名查找失败；找到真实日志后读取。执行原型未作为公共 MCP 功能提交，后续必须加长度/回显检查 |
| 本地 JVM 无法启动 | 原生 AE 日志在创建 Java 报表对象时以 RC=8 结束，尚未打开数据查询或写出工作簿；当前 PeopleTools 客户端目录中未找到 JVM |

原生执行失败发生在 `GM_DEPT_XLSX`（本地过程实例 397097），不是最终克隆 `GM_DEPT_XL4` 的执行通过证据。当前浏览器也没有现成的 HRDEV Web/Process Scheduler 会话。只读环境诊断还确认：远端无法解析数据库登记的 HRDEV Web 主机名，直接访问相应 IP:8000 也无法连接；当前客户端安装根内未找到 jvm.dll，没有改 ACL、安装 Java 或改全局环境。[环境诊断截图](images/acceptance-ae-properties-20261105/runtime_web_probe.png)仅说明该登记入口不可用，不等于所有调度器都不可用。

后续优先补齐 PSIDE 本地的 Java/报表运行环境：PSIDE 本身可通过 Edit/Run Program 执行 AE 并向它所在的远程 Windows 写文件，调度器是另一条可选路径。进一步只读确认 pside.exe 为64位，Oracle客户端目录找到的旧JVM文件版本为5.0.170.4和5.0.110.3，未拿来替换或加载；需要与PeopleTools8.57.11匹配的64位Java以及HPS/POI依赖。新结论与证据见 [Project文档的执行边界](projects.md)。具备执行依赖后，先确认 HpsReportDefn 的 String[] 方法兼容和输出目录，再实际运行最终 AE，按原生 COMPLETE/RC、实际工作簿格式、运行时数据库行数、60 列、中文、前导零和时间精度验收。74,762 是本次查询时的行数，不能当作未来运行的固定断言。创建/编译验收不替代这些项目。
