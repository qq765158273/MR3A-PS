# 2026-11-04 真实创建验收截图

以下为既有成功 MCP 调用导出的原始 1920×1080 PNG，按字节复制，没有缩放、裁剪或修改画面。截图来自远程桌面 canvas，未包含浏览器地址栏或登录凭据。完整结果及 DBX 验收见 [验收记录](../../acceptance.md)。

| 截图 | 展示内容 | 本机原始路径（相对 `psauto/out/objects/`） |
| --- | --- | --- |
| [Field 已保存](field-saved.png) | GM_MCP_FLD13 的 Character、长度 11 和标签 | `20261104_152040_039740/050_PSIDE_CreateField_Saved.png` |
| [Record Key 属性](record-key-properties.png) | GM_MCP_EMPLID 的 Key、Search Key、Listbox | `20261104_164647_935317/099_R_AttrOK.png` |
| [Record Alternate 属性](record-alternate-properties.png) | EFFSEQ 的非 Key、Alternate Search Key、Listbox | `20261104_164647_935317/171_R_AttrOK.png` |
| [Record Build 反馈](record-built.png) | GM_MCP_REC3 为 SQL Table，输出面板显示 Build 结果 | `20261104_164647_935317/208_R_BuildFinished.png` |
| [Step04 代码已保存](ae-step04-saved.png) | GM_MCP_AE4 的 PeopleCode 编辑器和保存反馈 | `20261104_171343_260521/160_A3_PSIDE_CodeEditorSaved.png` |
| [四步 AE 已保存](ae-four-steps-saved.png) | Step01–04 的 SQL/PeopleCode 结构，代码编辑器已关闭 | `20261104_171343_260521/166_PSIDE_CreateAE_Saved.png` |
| [空白操作台](workspace-idle.png) | AE 对象关闭后的最终操作台 | `20261104_171343_260521/170_PSIDE_CreateAE_SavedAndClosed.png` |

Maa 节点截图记录识别时的画面；例如 `R_AttrOK` 是属性设置完成、点击确定之前的画面。截图用于人工查看证据，程序是否成功仍由 Pipeline 终点及 DBX 查询分别判断。

这里的 REC3 截图早于复选框点击后确认的补强；补强的回归使用 `tests/fixtures/vision/` 下的前后状态裁剪。这组截图不冒充补强后重新建表的在线验收。

补强后已完成 GM_MCP_REC4 的完整重跑，见 [新一轮截图及 DBX 验收](../acceptance-record4-20261104/README.md)。
