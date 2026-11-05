# 审核修复后的正常链路补测

2026-11-05，主控新启动 MCP 服务，用最终修复代码创建 Character Field `GM_FIX_FLD`：长度 11，label_id=GMFIX，long_name=GM Review Fix Field，short_name=GM Fix。保存、关闭并释放工作台，整次进程调用约 60.224 秒。

原生 40 个节点全部完成，0 扫描重试、0 节点失败、0 动作失败；唯一候选未命中为正常查重分支。[summary](summary.json) 的阶段相加与原生事件计时一致。官方 CLI 预期及实际 settle 均为 0，[计时摘录](timings_excerpt.json) 记录 Pipeline 48.232 秒、导出 5.820 秒。

[MCP 原始返回](mcp_result.json) 为 saved_and_closed、saved:true、workspace_ready:true、evidence_status:complete、next_operation_allowed:true。新增结果分离及终态提取与正常完整流程兼容。

[保存后截图](field-saved.png) 与 [关闭后空白台](field-idle.png) 均为 Maa 的 1920×1080 原图。本机完整证据：`out/objects/20261105_154759_444124/`。

DBX 使用 ps-dev / HRDEV 只读验收：

```sql
SELECT F.FIELDNAME,F.FIELDTYPE,F.LENGTH,L.LABEL_ID,L.LONGNAME,L.SHORTNAME
FROM PSDBFIELD F JOIN PSDBFLDLABL L ON L.FIELDNAME=F.FIELDNAME
WHERE F.FIELDNAME='GM_FIX_FLD'
```

| FIELDNAME | FIELDTYPE | LENGTH | LABEL_ID | LONGNAME | SHORTNAME |
| --- | --- | --- | --- | --- | --- |
| GM_FIX_FLD | 0 | 11 | GMFIX | GM Review Fix Field | GM Fix |

(1 row, 18ms)

[历史四次事件回放](historical_events_replay.json) 是用新终态函数读取既有 events 的兼容校验，不能算作重新创建四个对象。错误计数、磁盘写入及恢复异常由离线/故障注入验证，见 [修复说明](../../reliability_fixes.md) 和 [独立复核](../../pshelp_reliability_review.md)。
