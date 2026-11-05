# 逐节点证据导出接入真实 MCP

2026-11-05，主控启动新的 stdio MCP 服务实例，加载本轮源代码及既有 `psauto-fast / settle=0` 配置，通过 `create_record` 创建 `GM_EXP_REC`，复用已存在的字段 `GM_OPT_EMPLID`、EMPLID、EMPL_RCD、EFFDT、EFFSEQ。五字段顺序、属性、HRAPP 和 Build 参数与此前 GM_OPT_REC 相同，仅 Record 名称不同。

完整调用 230.34 秒；208 节点全部完成，20 次正常候选未命中，0 识别轮次重试、0 节点失败、0 动作失败。MCP 返回 `saved_and_closed`、`built:true`、`workspace_ready:true`、`evidence_status:complete`、`next_operation_allowed:true`。保存、Build 和关闭均由原生 Pipeline 判断，数据库只在结束后只读验收。

业务原生事件跨度 200.719 秒；证据导出 27.565 秒，明确使用 `streaming`。228 张 raw 输入（含 20 个失败候选）全部保留映射，去重为 100 张 PNG。所有 208 节点均有原生计时。

本轮整体比此前 GM_OPT_REC 的 169.959 秒慢，不能作为真实业务提速样本。两次相隔约三小时，CLI 实际 settle 均为 0；本轮原生执行阶段就比历史增加约 56 秒，发生在证据导出之前。截图传输累计 28.806→58.517 秒，中位数 132→205ms、最大值 367→1949ms；81 次点击累计 18.560→33.932 秒。截图及输入调用变慢解释了大部分差值，但底层系统/浏览器变慢的原因未单独定位。节点数、动作数和动作后等待（35.946→36.044 秒）相同，没有出现新增重试或业务判断。

导出本轮 27.565 秒也高于旧真实样本 23.546 秒，包含失败候选详情和不同现场运行条件，不用它声称导出提速。性能结论以同一离线原生输入的独立进程对照为准；该对照主要证明内存收益，见 [导出性能](../../performance/evidence_export.md)。

本机完整证据：`psauto/out/objects/20261105_171830_968491`。仓库保留 [MCP 返回](../../performance/export/export_live_result.json)、[请求](../../performance/export/export_live_request.json)、[原生汇总](../../performance/export/export_live_summary.json)、[含导出分项的 timings](../../performance/export/export_live_timings.json)、[208 行节点计时](../../performance/export/export_live_nodes.csv) 和 [DBX 验收](dbx.md)。

以下为运行时原始 1920×1080 PNG 的直接副本，没有缩放或重新编码：

- [保存后对象](PSIDE_CreateRecord_Saved.png)
- [Build 1 条记录、0 错误、0 警告](R_BuildFinished.png)
- [关闭后空白工作台](PSIDE_CreateRecord_SavedAndClosed.png)
- [任务结束的最终截图](workspace.png)
