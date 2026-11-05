# Project 保存验收证据

目标 GM_DEPT_EXPORT：显式AE GM_DEPT_XL4、Record GM_DEPT_AET，每项选择全部原生Related Definitions；保存后释放为空白Untitled。

- [请求](request.json) / [MCP返回](mcp_result.json)
- [55行节点CSV](nodes.csv) / [summary](summary.json) / [timings](timings.json)
- [AE关联已选](ae_related.png) / [AET关联已选](aet_related.png)
- [工程已保存](project_saved.png) / [工作台已释放](workspace_ready.png)
- [DBX成员和编译长度](dbx.json)
- [普通127项：58通过/69跳过](unit_tests.txt)
- [Project模块：2参数+3native，5项通过](native_tests.txt)

原生跨度37.250秒，55/55节点完成、0节点/动作失败，2次扫描重试、3次候选未命中；证据导出另约9.862秒。显式对象数2不等于原生成员数，DBX返回10条。完整本机目录：psauto/out/objects/20261105_222241_025083。

[本地JVM诊断](local_pside_jvm_diagnosis.png)是环境检查，不代表AE或Excel执行成功。参数与判决见 [Project文档](../../projects.md)。

同一 MCP 的 [重名拒绝后继续创建三类型工程](continuation_results.json)，以及 [DBX：原工程时间戳/成员未变、三类型工程12成员](continuation_dbx.json)。三类型调用的 [字段及关联已选截图](field_related.png)、[节点日志](all_types_nodes.csv) 和 [原生summary](all_types_summary.json) 另存。重名调用是预期拒绝，不计保存成功。

最终P2补强回归（修复前原始证据继续保留）：[请求](fixed_request.json)、[MCP返回](fixed_mcp_result.json)、[57行节点](fixed_nodes.csv)、[summary](fixed_summary.json)、[timings](fixed_timings.json)、[末端已选](fixed_record_end.png)、[滚动后首部已选](fixed_record_top.png)、[DBX](fixed_dbx.json)、[最终128项58通过70跳过](fixed_unit_tests.txt)、[最终Project模块6项通过](fixed_native_tests.txt)。目标GMPRJFIX01，原生44.969秒，0节点/动作失败；与业务主工程GM_DEPT_EXPORT成员一致。

名称搜索返回相近工程但被身份检查阻止的样本：[请求](guarded_lookup_request.json)、[返回](guarded_lookup_mcp_result.json)、[失败summary](guarded_lookup_summary.json)、[停止画面](guarded_lookup_after.png)。未保存、未计通过，未自动重放。

[独立审核报告](../../pshelp_project_review.md)保留初审、隐藏首部P2及定向修复关闭依据；[初审独立native日志](peer_native_tests.txt)、[初审结果](peer_results.json)、[旧保护失效模型](peer_hidden_model.json)、[修复独立测试](peer_fix_test.txt)、[修复模型结果](peer_fix_results.json)按原始SHA归档。报告SHA是工作区字节；Git会规范化文本换行，提交字节对照见 [快照清单](sha256_snapshots.json)。
