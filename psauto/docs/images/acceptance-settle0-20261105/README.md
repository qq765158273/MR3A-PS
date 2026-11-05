# 0ms CLI 配置完整验收

2026-11-05，通过同一个 stdio MCP 服务实例，依次从空白操作台开始创建 Character、Date、Record＋Build、四步 AE。四次均返回 `saved_and_closed`、`workspace_ready:true`；Record 另 `built:true`。总历时 381.175 秒，409 个节点全部完成，0 轮次重试、0 节点失败、0 动作失败。代码身份保护包含最终 Step 完整边界补丁，AE 未执行。

每个任务 `timings.json` 均记录 `expected_settle_ms=0`、`effective_settle_ms=0`。Chrome 保持后台、视口 1920×897，识图原图保持 1920×1080。截图直接来自 Maa 原生帧。

| 对象 | 工具调用含证据导出 | Maa 事件跨度 | 节点数 | 本机原始目录 |
| --- | ---: | ---: | ---: | --- |
| GM_OPT_EMPLID，Character 长度 11 | 46.722 秒 | 40.156 秒 | 40 | out/objects/20261105_135947_478122 |
| GM_OPT_DATE，Date | 42.969 秒 | 36.860 秒 | 37 | out/objects/20261105_140034_214824 |
| GM_OPT_REC，五字段 SQL Table＋Build | 169.959 秒 | 144.735 秒 | 208 | out/objects/20261105_140117_227126 |
| GM_OPT_AE，SQL / PeopleCode / SQL / PeopleCode | 119.688 秒 | 100.859 秒 | 124 | out/objects/20261105_140407_205637 |

Character：[保存后](field-saved.png)、[关闭后空白台](field-idle.png)；Date：[保存后](date-saved.png)、[关闭后](date-idle.png)。

Record：[已保存](record-saved.png)、[Build 完成](record-build.png)、[关闭后](record-idle.png)。

AE：[Step04 保存反馈](ae-step04-saved.png)、[父窗口已保存](ae-saved.png)、[最终空白台](ae-idle.png)。

[DBX 查询及原始返回](dbx.md) 确认 Field 类型/长度/标签、五字段顺序与属性、HRAPP 物理表、三个 VALID 索引及 0 行；AE 的 MAIN 四步、S/P/S/P、两个 COUNT SQL、两段字段名循环及编译长度 564 均正确。数据库只用于验收，不参与创建或 Build 写入。

同一浏览器的 500ms / 0ms 只读对照、隔离 500/100/0ms 测量与完整日志见 [执行链路与配置说明](../../performance/settle_optimization.md)。原始 `events.json`、`report.json`、`timings.json`、请求及完整逐步截图保留在上述本机目录。
