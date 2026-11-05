# AE 属性自动创建验收

最终完整样本：`GM_DEPT_XL4`，state_record=`GM_DEPT_AET`、disable_restart=true、MAIN/Step01/PeopleCode。身份和空列表保护修复后，新 stdio MCP 创建 66.50 秒，75 节点完成，保存关闭、state_record_bound、restart_verified、properties_saved 均为 true。证据 complete，next_operation_allowed=true。

原生跨度 54.938 秒，其中扫描准备 12.687 秒、识别 12.657 秒、动作前 0.046 秒、动作 16.189 秒、动作后等待 13.234 秒、未归属 0.125 秒。扫描准备包含截图、扫描间隔和其他准备，不等同于纯截图耗时。3 次额外扫描、7 次候选未命中，0 节点/动作失败；候选未命中不等于业务失败。MCP 总时长另含约 10.104 秒证据导出及启动等开销，各口径不能重复相加。

本机完整目录：`psauto/out/objects/20261105_213633_731943`。仓库保留 [MCP 返回](mcp_result.json)、[参数清单与代码摘要](request_manifest.json)、[75 行节点日志](nodes.csv)、[原生 summary](summary.json)、[分项 timings](timings.json) 及 [最终 XL4 的 DBX 元数据/编译检查](final_dbx.json)。业务代码尚未运行验收，参数清单只保存代码摘要，没有提交试验 PeopleCode。

原始无损截图副本：

- [默认 AET 首行已绑定](AEProp_StateBound.png)
- [Disable Restart 已确认](AEProp_RestartVerified.png)
- [保存关闭、空白操作台](PSIDE_CreateAE_SavedAndClosed.png)

另一个分段样本 GM_DEPT_XLSX 实际执行的[原生 JVM 错误日志](ae_runtime_jvm_error.png)是原图局部直接裁剪，没有缩放或改像素。该次执行以 RC=8 结束，没有完成 Excel 导出；不计业务运行成功。[远端 Web 入口诊断](runtime_web_probe.png)也仅是环境探测，未成功调度 AE。

6 项原生属性测试的最终输出见 [native_tests.txt](native_tests.txt)，普通套件 121 项中 55 通过、66 跳过见 [unit_tests.txt](unit_tests.txt)。旧有 14 项原生视觉回归另通过，完整运行日志在本机 `out/dept_existing_vision_tests.log`。pshelp 在首次审核提出 P2/P3，修复后独立定向复测 2/2 通过，完整历史见 [独立审核报告](../../pshelp_ae_properties_review.md)，其 [独立测试日志](peer_fix_tests.txt) 与 [结果](peer_fix_results.json) 按报告 SHA 原样归档。不同批次有重叠，不能累加成整体通过数或长期成功率。

修复前 GM_DEPT_XL3 的首次样本保留在 `initial_*` 文件中：[初次 MCP 返回](initial_mcp_result.json)、[初次请求摘要](initial_request_manifest.json)、[初次节点日志](initial_nodes.csv)。[dbx.json](dbx.json) 是该历史样本 XL3/XLSX 的元数据及 XL3 源码检查，不能当作 XL4 的源码检查；[final_dbx.json](final_dbx.json) 专门对应最终 XL4。

完整设计、失败取舍和剩余执行条件见 [demo 记录](../../department_export_demo.md)。

审核报告 SHA 记录的是当时工作区的原始字节。本仓库强制 Git 文本使用 LF，部分 Windows 日志/源码原为 CRLF；[SHA 对照清单](sha256_snapshots.json)列出此次归档文件的工作区和暂存 Git 字节摘要，差异已确认仅为换行规范化。清单不包含其自身。
