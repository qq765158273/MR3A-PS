# 合并查询与 Record 卡点修复验收

2026-11-05，主控使用新启动的 stdio MCP 验证最终代码，Playwright CLI 实际 settle=0。业务由 Maa/MR3A Pipeline 操作原始 1920×1080 RDP 图像；DBX 只在操作结束后只读验收。

## 三次开发验证分别计数

| 对象 | 完整工具调用 | 结果 | 节点与处理 |
| --- | ---: | --- | --- |
| GM_RPC_REC | 119.94 秒 | failed，未保存 | 137 节点；选中字段边框被 OCR 读作引号，严格字段名拒绝通过；丢弃本次未保存草稿后才重测 |
| GM_RPC_REC2 | 180.22 秒 | partial，已保存且 Build，未关闭 | 标题框随机点击落在窗口图标上，打开系统菜单；开发收尾单独关闭并确认空白台，不追改原 partial 结果 |
| GM_RPC_REC3 | 173.22 秒 | saved_and_closed，built=true | 最终版本从头完成 207 节点，workspace_ready=true，证据 complete，next_operation_allowed=true |

每次失败均由服务阻止后续业务，不自动重放。重测由主控读取证据、明确处理本次草稿/已保存窗口、确认空白台后新建 MCP 服务实例进行；前两次不计最终版本成功样本。

失败证据、完整状态和节点计时分别保存为 performance/roundtrips 中的 [failed_roi](../../performance/roundtrips/failed_roi_result.json)、[partial_close](../../performance/roundtrips/partial_close_result.json)、[record3](../../performance/roundtrips/record3_result.json) 前缀文件；本机原目录依次为 `out/objects/20261105_175023_339465`、`20261105_180031_075459`、`20261105_180726_715320`。

## 最终完整调用

GM_RPC_REC3 原生事件跨度 144.187 秒，证据导出 27.449 秒。207 节点均有完整原生计时，0 节点失败、0 动作失败；共有 24 次候选未命中，其中包括 4 次额外扫描：查重对话框、Field1/2/4 插入对话框各等了一轮。它们只等待状态出现，没有重发输入；不能写成“零重试”。

Maa 阶段累计：截图/下一轮准备 32.757 秒、识别 33.926 秒、输入动作 41.503 秒、动作后等待 35.642 秒、动作前 0.079 秒、引擎未归属 0.280 秒，合计与事件跨度一致。导出后的 after.png 和进程启动/清理不属于这些节点时段。

相比上一轮较慢的 GM_EXP_REC（230.34 秒），本次恢复到约 3 分钟；与更早的 GM_OPT_REC（169.959 秒）整体接近。对象名、UI 状态、连接恢复、版本和时间不同，不能把跨时段差值全归因于本轮。真正同页只读 A/B 的截图 CLI 中位数为 180.5→76.7ms，含解码 227.4→123.7ms，12 对像素完全一致；此证据支持典型截图成本下降，不证明长尾消失或完整业务平均收益。

DBX 返回确认 GM_RPC_REC3 的五字段顺序及 USEEDIT 为 `8390689/8390689/8390689/8388656/8388656`，HRAPP 物理表、3 个 VALID 索引及 0 行。GM_RPC_REC 没有定义行，GM_RPC_REC2 与 GM_RPC_REC3 定义存在，与各次已保存事实一致。查询原始返回见 [dbx_record3.json](dbx_record3.json)。

## 同一 MCP 连续两次调用

随后在另一个新 MCP 实例的同一 stdio 连接中，顺序创建 `GM_RPC_F1`（Character 长度 11）和引用该字段的五字段 `GM_RPC_REC4`＋Build。Field 48.89 秒、40 节点；Record 175.53 秒、207 节点。两次都 saved_and_closed、workspace_ready=true、evidence_status=complete、next_operation_allowed=true；Record4 为 0 识别轮次重试、0 节点失败、0 动作失败，20 次正常候选未命中。

DBX 确认新 Field 类型 0、长度 11、标签 GMRPC、长短名称正确；Record4 第一字段确为 GM_RPC_F1，其余依次 EMPLID、EMPL_RCD、EFFDT、EFFSEQ，属性与请求一致；HRAPP、三个 VALID 索引及 0 行通过。该连续样本验证上一对象释放操作台后，同一服务接受并完成下一对象；仍不等于长期无人值守保证。

原始 [连续 MCP 返回](../../performance/roundtrips/continuity_results.json)、[DBX 返回](dbx_continuity.json)、[Field 汇总](../../performance/roundtrips/field_summary.json)、[Record4 汇总](../../performance/roundtrips/record4_summary.json) 和对应前缀的请求、timings、节点 CSV 已归档。图像：[Field 关闭后](field_workspace.png)、[Record4 保存](record4_PSIDE_CreateRecord_Saved.png)、[Build](record4_R_BuildFinished.png)、[关闭后](record4_workspace.png)。

## 原始截图

以下 PNG 均为原始证据的直接副本，没有缩放或重新编码：

- [第一次：字段边框误读](failed_roi.png)
- [第二次：系统菜单导致关闭未完成](partial_close.png)
- [最终：保存完成](PSIDE_CreateRecord_Saved.png)
- [最终：Build 1 条记录、0 错误、0 警告](R_BuildFinished.png)
- [最终：关闭后空白台](PSIDE_CreateRecord_SavedAndClosed.png)
- [最终：任务结束截图](record3_workspace.png)

实现、离线正反例、真实对照及验证边界见 [优化记录](../../performance/transport_roundtrips.md)。长期无人值守、隐藏页面长尾和其他版本仍需积累证据。
