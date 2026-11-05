# 全屏环境下的 Field15 与原生日志汇总验收

2026-11-05，用户将 Jump 浏览器切至全屏后，通过 stdio MCP 完整创建 `GM_MCP_FLD15`，保存关闭并回到空白操作台。运行时由 Maa JSON 判图和选择下一步。

- MCP 返回 `success:true, status:saved_and_closed, workspace_ready:true`。
- 45 个节点完整计时，1 次正常候选未命中、0 次额外识别轮次、0 次节点/动作失败；全部 `recognition.rule_passed:true`。
- Pipeline 约 81.199 秒；启动至结果落盘约 92.435 秒；证据导出约 5.112 秒。
- [自动生成的 summary.json](summary.json) 中各阶段加 `unattributed_ms` 等于原生事件跨度 81188ms。该文件按字节复制自运行证据，没有使用事后分析脚本生成。
- DBX 确认 Character、长度 11、GMEMPLID 标签、长/短名称及默认标签正确：[实际返回值](dbx.md)。

本轮明确验证了“输入 → Tab 移开光标 → 严格名称识别”的顺序。此前 Field/AE 的 Tab 错排在识别之后，不能消除识别时的插入光标；本轮修正了查重及 Save As 两处顺序。AE 的同类 JSON 顺序同步修正并经参数/schema 检查，本轮没有额外新建 AE。

业务截图仍是原始 1920×1080；canvas 分配 1920×1088，末尾 8 行裁掉。全屏浏览器视口为 1920×1024，当前 `document.visibilityState=visible`。只读补测中，CLI 空命令约 512ms，原始画布截图约 594–600ms；旧隐藏标签页曾约 1–1.65 秒。可见性影响浏览器计时器及是否需要刷新浏览器画面，因此不能把本轮 92 秒与 Field14 的 142 秒差值全部归因于代码。

全屏当前不需要隐藏页面刷新。另测全屏页面的完整截图刷新约 104–127ms、1×1 裁剪刷新约 35–49ms；后者尚未验证隐藏页面能否可靠刷新远程新帧，保留为未提交试验，正式控制器仍保留原有刷新保护。直接删除刷新会重现以前读旧画面的风险。

| 原始 PNG | 内容 | 原始引用 |
| --- | --- | --- |
| [Field 已保存](field15-saved.png) | 类型、长度和标签参数，保存反馈已通过 | `042_PSIDE_CreateField_Saved.png` |
| [操作台空闲](field15-workspace-idle.png) | 对象已关闭 | `044_PSIDE_CreateField_SavedAndClosed.png` |

截图为原始节点 PNG 的字节复制。完整原生日志、逐节点 ID/耗时、事件、请求和图像在本机 `psauto/out/objects/20261105_100510_036644/`，MCP 结果为 `out/field15_native_log_result.json`。
