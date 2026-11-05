# 2026-11-05 Pipeline 合并与截图刷新验收

截图均来自 Maa 原生运行时的 1920×1080 帧。完整证据在本机忽略目录，未用浏览器缩小后的画面识别。以下调用均为从空白台开始的完整 MCP 操作，并在保存、关闭后通过 DBX 只读验收，AE 未执行。

| 操作 | 本机原始证据 | 完整调用 |
| --- | --- | ---: |
| GM_AE_FAST，SQL / PeopleCode / SQL / PeopleCode | out/objects/20261105_115730_345882 | 353.254 秒 |
| GM_AUDIT_F，Character 长度 11 | out/objects/20261105_120343_749372 | 132.797 秒 |
| GM_AUDIT_DATE，Date | out/objects/20261105_120636_207766 | 120.253 秒 |

AE Step04 保存后：[原图](ae-step04-saved.png)；AE 父窗口保存后：[原图](ae-saved.png)；AE 关闭后空白台：[原图](ae-workspace-idle.png)。

Character Field 保存后：[原图](field-saved.png)；关闭后：[原图](field-workspace-idle.png)。

Date Field 保存后：[原图](date-saved.png)；关闭后：[原图](date-workspace-idle.png)。DBX 确认 Date 类型 4、长度 10 及标签，37 个节点全部完成。

[DBX 查询及原始返回](dbx.md) 确认四步顺序、动作 S/P/S/P、两段 COUNT SQL、两段字段名循环源码及编译长度 566；Field 类型 0、长度 11、标签均正确。

节点合并前后与截图分项测量见 [性能复核](../../performance/pipeline_audit.md)。两次 AE 总耗时接近，不将此次结果宣称为显著提速。GM_AE_BASE 是此前截图失败的部分对象，仅清场，不计完整成功。
