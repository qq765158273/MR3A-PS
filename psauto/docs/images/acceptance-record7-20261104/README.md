# 优化后的 GM_MCP_REC7 完整验收

2026-11-04，使用与 REC4 相同的五个字段、属性、HRAPP 表空间及 Build 参数，通过 stdio MCP 从空白操作台创建 `GM_MCP_REC7`，保存、Build 并关闭。

- 完整 MCP 返回 `success:true, saved:true, built:true, workspace_ready:true, status:saved_and_closed`。
- 208 个节点完成，12 次复选框点击后确认全部通过，0 次动作失败、0 次识别重试循环。20 次候选未命中均为正常分支。
- Pipeline 493.375 秒；启动到最终结果文件落盘 524.384 秒；独立计时的证据导出为 23.267 秒。
- DBX 六项只读验收通过：SQL Table、5 个字段、正确的 Key/Search/Alternate/Listbox 属性、HRAPP、3 个 VALID 索引、0 行。详见 [实际查询返回值](dbx.md)。
- 本机完整证据：`psauto/out/objects/20261104_205229_380875/`；请求/结果：`out/record7_performance_request.json`、`out/record7_performance_result.json`。

| 原始 1920×1080 截图 | 内容 | 运行目录中的源文件 |
| --- | --- | --- |
| [最后一个字段的属性](record7-attributes.png) | EFFSEQ 为非 Key，Alternate Search Key 和 Listbox 已选中 | `166_R_AttrSearchLabel.png` |
| [Build 完成](record7-built.png) | 当前 Record 的 SQL Table 和 Build 输出 | `204_R_BuildFinished.png` |
| [操作台空闲](record7-workspace-idle.png) | 已关闭对象，释放给下一操作 | `207_PSIDE_CreateRecord_SavedAndClosed.png` |

图片按字节复制，未缩放或修改。导出去重后，多个节点可引用同一个完全相同的原始帧；属性图由最后一次 `R_AttrOK` 的报告引用取得，源文件名是该帧第一次保存时的节点名。

性能基准和逐节点 CSV 见 [优化记录](../../performance/optimization.md)。REC5、REC6 的校准失败及分段收尾单独保留，不计为本次完整成功。
