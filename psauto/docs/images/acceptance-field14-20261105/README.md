# 优化后的 GM_MCP_FLD14 Field 验收

2026-11-05，通过优化后的 Field Pipeline 创建 `GM_MCP_FLD14`，类型 Character、长度 11、标签参数与既有 Field 测试一致，保存关闭并返回空白操作台。

- MCP 返回 `success:true, status:saved_and_closed, workspace_ready:true`。
- Pipeline 128.375 秒；从启动到结果落盘约 141.840 秒；45 个节点完成，动作全部成功。
- DBX 确认 FIELDTYPE=0、LENGTH=11，LABEL_ID=GMEMPLID，长/短名称及默认标签正确。

| 截图 | 内容 | 源文件 |
| --- | --- | --- |
| [Field 已保存](field14-saved.png) | 编辑页保存反馈 | `042_PSIDE_CreateField_Saved.png` |
| [操作台已释放](field14-workspace-idle.png) | Field 窗口关闭 | `044_PSIDE_CreateField_SavedAndClosed.png` |

截图为原始 1920×1080 节点 PNG 的字节复制；DBX 只读返回值见 [查询记录](dbx.md)。
