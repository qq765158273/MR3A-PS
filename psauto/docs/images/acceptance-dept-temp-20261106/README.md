# 部门临时表导出与61字段MCP验收

本轮功能样本是 `GM_DEPT_TMP`、`GM_DEPT_XL5` 和 Project `GM_DEPT_TEXP`。它们经过分段校准及编译修复，不能改称首次完整MCP成功。新的 `GM_DEPT_QA`（Record）和 `GM_DEPT_QAE`（AE）分别从空白操作台完成完整MCP，用于验证最终通用实现。

| 样本 | 本轮结果 | 原生节点/跨度 |
| --- | --- | --- |
| GM_DEPT_QA Temporary Table＋Build | 完整MCP成功，61定义/物理列顺序、四键、VALID唯一索引由DBX核对 | 889 / 632.828秒 |
| GM_DEPT_QAE 两步AE | 完整MCP成功，默认AET、临时表、Disable Restart、代码保存关闭齐全 | 108 / 89.516秒 |
| GM_DEPT_TEXP Project | 完整MCP成功，显式三定义，DBX共822关联成员 | 72 / 54.453秒 |
| GM_DEPT_TMP 校准收尾 | 分段设置四键、保存、Build、关闭；原首次失败保留 | 收尾117 / 63.313秒 |
| GM_DEPT_XL5 修复收尾 | 修正多变量初始化、SQL字面量1000字符限制后编译保存关闭 | 收尾11 / 10.953秒 |

`*_mcp_result.json` 是实际返回；`*_summary.json` 和 `*_nodes.csv` 来自Maa原生事件，`*_timings.json` 保留分项。Record完整回归另有109.563秒证据导出；AE/Project分别另18.052/17.791秒。原生跨度、Pipeline计时和工具总时长口径不同，不重复相加。不是与旧五字段样本的性能对照。

`dept_record_qa_dbx.json` 保存最终QA对象的61项定义、物理列、索引和QA AE编译结果。`dept_ae_dbx.json` 保存业务XL5默认AET/Restart/temp binding、Step01 SQL、Step02编译长度7369及完整源码分块。`dept_project_record_dbx.json` 保存Project成员分组及业务临时表类型/字段/列映射。DBX只有SELECT，不参与对象创建或Build写入。

主控重建XL5数据库PeopleCode为4048字符，保留字符串内容的token与当前payload完全相同；Step01 SQL也一致。pshelp独立复查并关闭两项编译P1，见[完整审核及追加说明](../../pshelp_department_temp_review_20261106.md)。业务校准表33/34列互换，但具名INSERT/SELECT保持映射；完整QA表顺序全部正确。源EFFDT不允许NULL、临时EFFDT允许NULL，未把唯一索引当作所有列的NOT NULL主键。

PNG是原生1920×1080截图的字节复制，没有缩放或修改；`sha256.json` 是归档字节摘要。初始失败返回单独保留，不计通过。完整本机路径见 `run_index.json`。

普通套件148项：68通过、80按环境跳过；新增4项原生图像测试和既有14项视觉回归通过。日志在本目录。没有执行AE或生成最终Excel，不把保存/编译/Project验收扩展为运行通过；JVM/Java方法、xlsx格式、内容、大行数及P2文件完成保护仍待运行验收。
