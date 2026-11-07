# 常用 Record 类型与 AE 临时表

2026-11-06，在原 MaaFramework / MR3A / Playwright CLI 链路上扩展。业务步骤和判决在 Pipeline JSON，Python 只绑定参数、类型分支和原生完成标记；SQL 通过剪贴板粘贴，识别保存反馈，不 OCR 回读正文。更新后需重新连接 MCP。

## Record 类型

| create_record.type | PSRECTYPE | view_sql | build |
| --- | --- | --- | --- |
| SQL Table | 0 | 不传 | 可选，创建表及索引 |
| SQL View | 1 | 必传 | 可选，创建数据库视图 |
| Derived/Work | 2 | 不传 | 不允许，无物理表 |
| Dynamic View | 5 | 必传，可明确提供动态 SQL 占位文本 | 不允许，仅定义与 SQL |
| Temporary Table | 7 | 不传 | 可选，标准 PeopleSoft 临时表及索引 |

SQL Table 和 Derived/Work 是既有能力；本轮新增其余三种。Query View、SubRecord、Materialized View、Oracle GTT 等额外选项不属于本次接口。Temporary Table 保持默认 GTT 状态；AE 实例数量与分配策略也保持默认，本轮没有创建专用实例池或执行 AE 来验证实例分配。

```json
{
  "name": "GM_MY_VIEW",
  "type": "SQL View",
  "fields": ["SETID", "DEPTID"],
  "view_sql": "SELECT SETID, DEPTID FROM PS_DEPT_TBL WHERE 1 = 0",
  "build": true
}
```

视图先保存命名的 Record，再进入该 Record 的 `.2 (SQL 定义)` 编辑器粘贴 SQL、保存并关闭，返回 Record 保存后才可 Build/关闭。业务成功额外要求 `R_ViewSQLSaved`，返回 `view_sql_saved:true`；仅有 Record 保存关闭标记不能代表 SQL 已保存。正文是原样参数，不被解释为 Pipeline 参数或 shell 命令；空/NUL/超过64KiB UTF-8的SQL在打开浏览器前拒绝。

SQL View 的 Build 明确使用 Create Views，关闭 Create Tables/Create Indexes；SQL Table/Temporary Table 使用表和索引，关闭视图。执行前再次确认所有选项和目标名称，继承已有 Skip existing、有限等待及原生 Build 完成/0错误/0警告判决。

标题识别只看必要区域。校准发现完整长标题把VW01误读为VWo1，缩小到对象标题区域后真实fixture可区分0/O；没有放宽对象名。Record 保存及 Build/关闭使用完整对象段与记录类型标识，拒绝前缀对象。新原生用例同时覆盖旧Work记录保存和新三种类型的错误radio状态。

## AE 参数

```json
{
  "name": "GM_MY_AE",
  "state_record": "GM_DEPT_AET",
  "disable_restart": true,
  "temporary_records": ["GM_KIND_TMP"],
  "steps": [{"type": "SQL", "code": "SELECT COUNT(*) FROM %Table(GM_KIND_TMP)"}]
}
```

`state_record` 是默认状态记录；`temporary_records` 是另外的 Temp Tables 列表。调用方应先准备 Temporary Table 定义。列表支持1–10个已有Record名、拒绝重复和非法名，按名称排序绑定固定行。每个名字都必须在Record List中严格识别，Add后在Selected对应行识别，所有请求行及TempsBound、PropertiesSaved原生标记齐全才返回 `temporary_records_bound:true`。

开始添加前检查Selected列表全部为空，不覆盖未知列表。静态控件模板通常0.85，启用Add还检查字形颜色，动态对象名用局部完整OCR；等待均有限，没有失败后回跳重放。Temp Tables改变后会出现已校准的“Insert updated Temp Table list into Project?”提示，识别完整提示及否按钮后选择否，避免创建操作隐式污染当前Project；工程归集仍由save_project完成。未知提示停止。

Disable Restart继续接受严格bool，省略保持默认；false与None不同。属性顺序为默认AET、临时表、Restart，再粘贴代码。AE结束改为完整父对象标题＋保存灰态＋活动关闭图标的定位点击，避免焦点不在MDI编辑器时Ctrl+F4无效；缺保存或错误前缀不会点关闭。

`create_ae` 的临时表实例数默认是3，可通过 `temporary_table_instances` 调整。绑定不等于实例池已经生成：Temporary Table Record 必须先 Build，PeopleTools 才会创建基础表和实例表；未 Build 直接运行会因物理实例表不存在而失败。Share Tables/Continue/Abort 等运行选项保持原生默认。本轮接口仍支持1–10张临时表；部门 AE 已实跑三实例池并验证 `%Table` 落到实例表，运行后数据保留。

## 完整 MCP 与 DBX 验收

| 样本 | 原生节点 | 原生跨度 | 结果 |
| --- | ---: | ---: | --- |
| GM_KIND_VW，SQL View＋Build | 85 | 64.250秒 | SQL已保存、物理VIEW为VALID |
| GM_KIND_DV，Dynamic View | 67 | 52.094秒 | SQL已保存、没有创建物理VIEW |
| GM_KIND_TMP，Temporary Table＋Build | 99 | 69.406秒 | TABLE/INDEX均VALID |
| GM_KIND_AE，AET＋一张临时表＋Disable Restart | 83 | 58.000秒 | 三项属性、SQL保存关闭均通过 |
| GM_MORE_AE，AET＋两张临时表＋Disable Restart | 90 | 62.656秒 | 两成员列表、属性、SQL保存关闭均通过 |

五次均0节点/动作失败，evidence complete、next_operation_allowed=true；不同批次有2–4次扫描重试、6–10次候选未命中，它们不是动作失败。证据导出另约8.5–13.4秒，各口径不重复相加。三种Record在同一个MCP实例串行完成；AE的一表/两表分别为新stdio调用。两个AE的DBX状态均Disable Restart=Y、默认GM_DEPT_AET/Y，PSAEAPPLTEMPTBL分别1/2行，TEMPTBLINSTANCES仍0，Step01 SQL为传入的%Table查询。

普通套件140项：64通过、76显式跳过。新增视觉5项通过、临时表模块3项通过（其中2项参数与普通套件重复）、原AE属性6项及既有视觉14项回归通过。批次有重叠，不累计整体成功率。图、逐节点CSV、参数与原始DBX见 [验收证据](images/acceptance-common-kinds-20261106/README.md)。

校准中出现过未绑定的实验override、0/O长标题误识别、分段执行缺失Maa前置ROI缓存、尚未释放工作台等失败，均停止并保留在本机out，不计完整调用通过。确认状态后只对本次自建测试对象恢复/继续，最终可信验收使用上述五次从头MCP。实验脚本未作为公共API提交。

## 部门业务代码的独立审核

pshelp已直接用DBX读取实际PeopleCode及对象：[正式报告](pshelp_department_code_objects_review.md)。60列表头/SQL/物理列顺序、AE/AET/Project成员已核对一致；发现文件完成/异常收尾保护缺口P2，以及日志仍写旧GM_DEPT_XLSX的P3。实际xlsx格式、Java方法、大行数/内存和文件内容仍未运行验收，本轮未修改GM_DEPT_XL4业务代码。原始数据库源码、共享helper及业务数据探针留在本机out/pshelp_department_code_objects_evidence；仓库归档报告与摘要，不把这些其他对象源码或业务行纳入功能实现。
