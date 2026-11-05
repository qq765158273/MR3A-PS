# 审核问题修复与验证

2026-11-05，修复相对基线 `548a63e` 的三项既有问题。来源为 tmux pshelp 在本机 `out/pshelp_current_review_reply.md` 的独立审核：Build 数字子串误判、证据故障覆盖已完成业务、恢复客户端清理遗漏。原 settle=0 完整调用和 DBX 样本仍成立；这轮优先修复故障语义与清理，导出性能单独安排。

## Build 成功计数

`create_record.json` 中 `R_BuildFinished` 的原规则会接受“10 条错误”“10 条警告”，甚至“10 条记录、20 条错误和 30 条警告”。新规则限定完整行及数字边界，只允许处理 1 条记录、0 错误、0 警告；保留原有局部 ROI、SQL 在线执行和活动编辑器检查。

原生 Maa 测试使用已发布 Record 成功截图的 900×45 裁剪，以及同位置生成的计数反例。15 个场景中真实/合成的 `(1,0,0)` 通过，0/10/11/100 条记录、1/10/20/100 条错误或警告及混合非零计数均停止，不能进入关闭动作。测试中的关闭键由离线控制器捕获，不操作真实桌面。

## 业务事实和证据结果

服务在证据导出之前，从 Maa 原生事件取得保存、关闭和 Build 事实：公开 `job.job_id` 对应 `task_id`，成功节点使用 `node_details.name` 和 `completed:true`。不采用可能指向上一节点的 `details.name`，不将其他任务、识别候选或未完成节点计为成功，也不为提取终态而读取全部节点图像。

接口新增字段：

| 字段 | 含义 |
| --- | --- |
| success / status / saved / built | 已知业务结果，仍要求任务成功及相应保存、关闭、Build 终点 |
| workspace_ready | 本次已知工作台事实；未检查的工作台不推断为空闲 |
| evidence_status | complete：主要证据和辅助证据正常；partial：主要导出完成但辅助证据/清理有故障；failed：主要导出未完成 |
| evidence_errors | 出错阶段和异常说明，独立于业务结果 |
| operation_error | 执行或 Agent 生命周期异常；诊断文件无法写入时仍随返回提供 |
| next_operation_allowed | 服务是否允许下一次任务进入；调用方应与业务结果一起读取 |

例如，任务确已保存关闭，但证据导出失败时仍返回：

```json
{
  "success": true,
  "status": "saved_and_closed",
  "saved": true,
  "workspace_ready": true,
  "evidence_status": "failed",
  "evidence_errors": [{"stage": "task_evidence", "error": "OSError: disk full"}],
  "next_operation_allowed": false
}
```

服务随后拒绝新业务，保留原任务的已知完成事实，不重放。错误报告和最终 timings 写入均独立兜底，诊断故障不再盖掉已经构造的结果。参数及 override 文件在浏览器操作前准备；这些文件单独写入失败也会停止，后续响应不会凭空声称工作台已关闭。

阻塞状态按实际原因表达：工作台未释放为 workspace_not_ready；证据故障为 evidence_unavailable；任务已经开始但 wait 或 Agent 退出抛错为 operation_stopped；不确定的 CLI 通信状态仍为 session_stopped。若异常发生时已经确认保存关闭，仍保留该事实，同时 next_operation_allowed=false。只有重启并排查故障后才继续接收新业务。

## 恢复与订阅清理

`recover_idle_session` 的探针整个使用区间由 finally 管理，成功、初始探针失败、恢复失败、模拟断线前置失败和原生后置检查失败均尝试 stop。`connect_recovery_controller` 在控制器构造、截图尺寸设置或连接失败时释放已创建 session；成功时由调用方接管。

EvidenceSink 增加幂等 close：注销成功后清空 sink_id，避免正常导出和 finally 清理时重复注销。服务 finally 尝试清理 sink 和客户端；一项失败仍执行另一项。恢复过程的三个 sink 使用标准库 closing 管理，任务或导出抛错也会清理；本轮没有引入新的识图或流程引擎。

## 验证

本机日志位于 `out/review_fix_service_tests.log`、`review_fix_recovery_tests.log`、`review_fix_native_vision.log`、`review_fix_evidence_tests.log`，四份既有真实事件的终态回放为 `out/review_fix_real_trace_replay.json`。

最终服务 20 项、恢复清理 9 项、原生识图 12 项、既有 evidence 4 项通过。普通全套 103 项中 46 通过、57 项按集成开关跳过；上述分别报告，不将不同批次或重叠测试相加为整体成功率。

- 服务故障注入覆盖导出、after.png、timings、错误报告、预备文件、sink 清理、wait 和 Agent 退出等路径；核对已知事实、后续阻塞、只提交一次任务以及客户端清理。
- 恢复模拟覆盖成功及各失败出口，核对已创建客户端和事件订阅释放。
- 原生识图覆盖 Build 数字边界、进入下一节点的动作保护，并用真实 Maa 任务验证终态事件提取。
- 既有 evidence 测试继续验证原生重试/失败事件、像素一致和截图去重。四份历史 Field/Date/Record/AE events 回放与原验收结论一致，属于兼容回放，不是重新执行四次业务。

Windows 测试清理曾遇到 WinError 145；测试夹具仅对此临时目录删除错误作最多三次、间隔 50ms 的清理重试，其他错误仍失败。该逻辑不用于业务输入、保存或 Build。

## 复核与边界

已将修复差异直接发送给 tmux pshelp 的现有 agent。它对中间快照指出：完整终态之后 wait 抛错、或 Agent 退出抛错时，还可能放行下一业务；本轮已补独立 operation_stopped 阻塞及对应反例，提前返回也统一提供 next_operation_allowed=false。

主控已主动读取 pshelp 在 15:49:24 核对的正式报告，9 个源码/测试/图片哈希均与最终工作区一致。其结论为：在授权的只读、离线与内存模拟范围内，三项原问题及补充边界均已关闭，没有尚未修复的确定阻塞问题。它独立完成 175 种 Build 计数组合、10 类 service 故障矩阵和 6 类恢复清理模拟；这些不冒充浏览器或数据库实测。正式报告见 [pshelp 原文](pshelp_reliability_review.md)。

主控另补正常真实调用：新 MCP 实例创建 `GM_FIX_FLD`，约 60.224 秒、40 节点、0 扫描重试/0 动作失败，保存关闭并回到空白台，返回 evidence_status=complete、next_operation_allowed=true；DBX 确认 Character 类型、长度 11 与标签。此次正常链路、API 返回和证据导出均使用最终代码；记录见 [MCP 与 DBX 补测](images/acceptance-review-fixes-20261105/README.md)。没有重新执行整组 Record/AE，Build 非零计数、磁盘和清理故障仍以离线反例验证。

故障注入和计数反例使用离线环境，没有制造真实磁盘满、真实 Build 错误或网络故障。长期资源占用、真实迟到绘图，以及逐节点导出的内存和耗时改善仍是后续验证项目。
