# 复选框补强后的 GM_MCP_REC4 完整验收

2026-11-04，通过 stdio MCP 的 `create_record`，从空白操作台创建 `GM_MCP_REC4`，设置五个字段属性，保存到 HRAPP，Build 表及索引，关闭对象。UI 流程全由 Maa JSON 执行，运行时没有 AI 决定操作。

- MCP 返回 `success:true, status:saved_and_closed, saved:true, built:true, workspace_ready:true`。
- 226 个节点完成，12 次点击后的勾选/未勾选状态检查全部通过。
- Maa 任务事件跨度约 906 秒；从后台进程启动到 MCP 结果文件落盘约 972 秒，包含启动与证据导出。
- 完整原始记录：`psauto/out/objects/20261104_183010_506938/`；MCP 结果：`psauto/out/record4_guard_result.json`。原始运行目录保留在本机忽略目录。
- [DBX 六项只读查询及实际返回值](dbx.md)：字段顺序及 Key/Search/Alternate/Listbox 属性正确，SQL Table，HRAPP，三个 VALID 索引，0 行。

以下 PNG 均按字节复制自原始 1920×1080 节点截图，没有缩放、裁剪或修改画面。

| 截图 | 源文件 | 证明的界面状态 |
| --- | --- | --- |
| [前三项属性确认](record4-key-confirmed.png) | `101_R_AttrSearchCheckResult.png` | GM_MCP_EMPLID 的 Key/Listbox/Search Key 已勾选；最后一次点击的状态确认节点成功 |
| [取消 Key 后确认](record4-uncheck-confirmed.png) | `156_R_AttrKeyUncheckResult.png` | EFFDT 的 Key 已取消；取消勾选后的状态确认节点成功 |
| [非 Key 字段属性](record4-alternate-properties.png) | `183_R_AttrOK.png` | EFFSEQ 保持非 Key，Alternate Search Key 与 Listbox 已选中 |
| [Build 完成](record4-built.png) | `220_R_BuildFinished.png` | Build 输出通过完成检查 |
| [操作台已释放](record4-workspace-idle.png) | `225_PSIDE_CreateRecord_SavedAndClosed.png` | 本次 Record 已关闭，回到空白操作台 |

在这次完整成功之前，17:56 启动的一轮测试在查重阶段进程中断，未保存 Record。DBX 确认 GM_MCP_REC4 不存在后，使用已有 `PSIDE_CancelOpenDialog` Pipeline 取消遗留查重窗口，再由空白操作台检查放行。中断证据保留为 `out/objects/20261104_175655_634418/` 和 `out/record4_interrupted.json`，不计成功；取消窗口的证据为 `out/runs/20261104_182955_594013/`。
