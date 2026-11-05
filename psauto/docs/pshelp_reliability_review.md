# pshelp 修复复核原文

2026-11-05，现有 tmux pshelp agent 的独立只读复核；来源为本机 out/pshelp_review_fixes_reply.md。下文保留正式报告原文及其快照哈希。主控之后完成的真实 MCP 补测另见 [补测证据](images/acceptance-review-fixes-20261105/README.md)。

2026-11-05，pshelp 回复主控 ps：三项修复的独立只读复核。

本轮标识：`fixes-review-548a63e-worktree-20261105`。收到主控补充消息后，再次核对最终源码快照的时间为 **2026-11-05 07:49:24 UTC（15:49:24 +08:00）**，九个文件均与本报告哈希一致。仓库 `C:/Users/t-wangsen05/Desktop/MR3A-PS`，origin [qq765158273/MR3A-PS](https://github.com/qq765158273/MR3A-PS)，分支 `feat/psauto-jumpserver`，基线 HEAD 仍为 `548a63e6c81f6df706c8522b3b8a2eb086bf`。审查对象为用户列出的九个工作区文件，包含两个新增文件；其余用户改动不属于本轮。

本次在当前 agent 完成，没有启动其他 agent。仅读取指定源码、原始历史证据与已有测试日志，并执行提取实际源码 AST 的纯内存故障注入、历史事件重放、正则矩阵及图片像素比较。所有故障注入的路径、控制器、任务和客户端均为内存替身，没有启动浏览器、操作桌面、连接数据库、创建对象、修改源码、写测试文件或提交。只写本报告，原 `pshelp_current_review_reply.md` 保持历史原样。

结论：**最终工作区快照在本轮授权的只读、离线与内存模拟范围内通过；三项原问题及审核中发现的补充边界均已关闭，未发现尚未修复的确定阻塞问题。** 审核期间工作区补充了请求写入失败阻塞、工作台事实保留、恢复 sink 清理及完整终态后的异常阻塞；均已重新核对。以下结论仅对应末尾列出的文件哈希，不能改称原 HEAD 已修复，也不能替代真实业务端到端验收。

1. **复核中间发现的 P2，最终已修复：完整终态之后的外层异常曾放行下一任务。** 对应最终修复位置：[service.py:147](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/psauto/objects/service.py:147)，放行条件位于同文件第 200 行。中间快照只记录 `operation_error` 并恢复业务事实，没有设置异常阻塞。以下保留当时的触发条件，明确区别于最终通过状态。

   **中间复现 A：业务终态齐全，但 wait 抛错。** 用当时的 `ObjectService` 和 `_business_result` 实际源码，构造同一 `job_id=1` 的 Saved、SavedAndClosed 成功事件，均含 `node_details.completed:true`，`job.succeeded=true`；令 `job.wait()` 抛 `RuntimeError`，其余诊断文件与清理成功。异常分支保留了已知业务事实，但跳过导出后曾返回 `evidence_status:'failed'`、`next_operation_allowed:true`。同一 service 的第二次调用仍提交任务。这是证据不完整时错误地允许下一任务开始，并非重放第一次任务。

   **中间复现 B：业务和导出成功，Agent context 退出抛错。** 令 `MR3AAgent.__exit__` 抛 `RuntimeError`，结果曾保留 `success:true` 和已关闭事实，同时仍返回 `evidence_status:'complete'`、`next_operation_allowed:true`；下一次调用仍提交业务。Agent 清理错误当时未进入阻塞。

   上述均为纯内存故障注入，未声称 Maa 或现场 Agent 已真实发生这些异常。原来的 wait 异常测试只覆盖 Saved 已出现、尚未 Closed 的部分完成路径，不能覆盖完整终态后的异常。

   **最终处置与独立复验：** 当前源码增加 `_operation_blocked`，业务开始后的外层异常将其置位；第二次调用返回 `operation_stopped`，使用 `_last_workspace_ready` 保留已关闭事实。放行条件也包含该标志。最新测试新增完整关闭后的 wait 异常、Agent 退出异常两个反例。用关闭此缺口的 service 快照 `f831c09782e4897b58bfff618376ad17e7f10086ff055a9f7c60c1ad91e766d5` 的实际源码重新注入 A/B，均得到 `saved:true`、`workspace_ready:true`、`next_operation_allowed:false`，第二次为 `operation_stopped`，合计只提交 1 次；sink 与 client 均清理 1 次。Agent 情形的 `evidence_status:'complete'` 继续准确表示文件导出完整，操作阻塞单独表达清理异常。随后最终快照仅为另两个提前返回补齐 next_operation_allowed，核心阻塞逻辑保持。因此此项不再是最终快照的未解决问题。

已通过的修复范围：

- **Build 计数边界。** [create_record.json:8163](C:/Users/t-wangsen05/Desktop/MR3A-PS/assets/resource/pipeline/PSIDE/create_record.json:8163) 改为完整行和数字边界。独立文本矩阵覆盖记录数 `{0,1,2,10,11,20,100}`、错误和警告数各 `{0,1,10,20,100}`，共 **175 种组合，0 不一致**，仅 `(1,0,0)` 通过。原 ROI、SQL 在线执行和活动窗口检查没有改变。新增 `build_success_feedback.png` 为 900×45，其像素与本机既有 `204_R_BuildFinished.png` 在 `(10,938)` 的对应裁剪完全一致。已有原生 12 项日志包含真实裁剪、合成数字反例、错误计数不得发送关闭键；本次没有重跑 OCR，也未制造真实 Build 错误。
- **终态事件与任务 ID。** [service.py:26](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/psauto/objects/service.py:26) 使用公开 `job.job_id`，与实际 Maa 绑定的整数 job_id 类型相符；以 `task_id` 过滤顶层任务，并从 `Node.PipelineNode.Succeeded` 的 `node_details.name`、`completed:true` 提取事实。原始日志中 `details.name` 确会指向前一节点，例如关闭终态的该字段可为 `F_CloseSaved`，因此当前使用 node_details 是必要的。没有读取 `detail.nodes` 或图像。将当前函数分别重放四份旧完整调用的 events，Field、Date、Record、AE 都得到正确 saved/closed，Record 另得到 built；这是旧事件与新函数的兼容校验，不是新修复的四次端到端验收。
- **主要证据故障不覆盖业务结果。** 独立内存注入 export、after.png、timings 写入、sink.close、session.stop 失败，已知 saved/closed/built 均保留，无 finally 写盘异常逸出覆盖成功返回。导出失败为 failed，后续辅助证据失败为 partial；相应错误进入 evidence_errors，下一调用被阻塞。session.stop 失败另使会话停止标志生效，没有重放原动作。
- **工作区补充的 preflight 和工作台事实修复。** 最终源码将 mkdir/request.json/pipeline_override.json 故障记录为 `request_evidence` 并阻塞；只让 request.json 失败、其他写入成功时，也不连接浏览器，第二次为 `evidence_unavailable`。所有写入均失败时仍返回结果。`_last_workspace_ready` 保存上一结果事实，尚未连接/识别工作台的 preflight 失败之后，第二次仍为 `workspace_ready:false`，不会凭证据阻塞标志制造“已关闭”事实。完整关闭后的导出失败则继续保留 true。之前中间快照的这两个缺口已在最终快照修正。
- **服务 sink 与客户端清理。** [evidence.py:65](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/psauto/evidence.py:65) 的 close 成功后清空 sink_id，因此成功导出后 service finally 再调用不会重复注销。导出失败时 service finally 仍会尝试注销，注销失败也不会跳过客户端 stop。关闭逻辑不依赖后续错误报告写盘成功。
- **恢复客户端和恢复 sink。** [recover_session.py:34](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/recover_session.py:34) 的 probe 使用整个区间的 finally；三个恢复任务的 EvidenceSink 都已用 `closing(...)` 包围。[recovery.py:95](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/psauto/recovery.py:95) 在控制器构造、尺寸设置或连接失败时释放 session。最终恢复源码的独立内存校验覆盖成功、恢复导出失败、原生后置检查导出失败、模拟断线前置导出失败、任务 wait 失败、sink.close 抛错六类情况；所有已创建客户端均尝试 stop，所有已创建 sink 均尝试 close。先前中间快照遗漏恢复 sink 的问题已经修正，不列为当前缺陷。

测试证据口径：主控提供的日志在审核期间更新。最终读取到服务 **20 项通过**（0.566 秒）、恢复清理 **9 项通过**（0.112 秒）、原生识图 **12 项通过**（32.219 秒）、既有 evidence **4 项通过**（1.113 秒）。对应文件分别是 `psauto/out/review_fix_service_tests.log`、`review_fix_recovery_tests.log`、`review_fix_native_vision.log`、`review_fix_evidence_tests.log`。采用最终完整 OK 日志，不将旧的 15/18 项、8 项或过程中的失败尝试累加为通过数。上述为读取主控日志的结果；本 agent 没有重跑这些测试套件，也没有把不同时间的日志描述为同一轮完整集成测试。

本轮 service 核心逻辑的独立纯内存矩阵包含正常成功、导出失败、after.png 失败、timings 与 error.txt 同时失败、sink.close 失败、session.stop 失败、全部写入失败、仅请求写入失败、完整终态后 wait 失败、Agent 退出失败，共 **10 类，0 不一致、0 异常逸出**。每类都检查第二次调用：正常情况可继续；故障情况不再提交下一任务；preflight 两类均为 0 次连接和提交；已提交业务的故障类均只提交 1 次。恢复流程另有上述 6 类内存清理验证。最终 service 快照的 session_stopped/workspace_not_ready 两个提前返回也分别用实际类源码做内存验证，均明确 `next_operation_allowed:false`。这些结果不冒充原生浏览器、数据库或 Maa 集成测试。

接口一致性建议也已在最终快照落实：session_stopped 与 workspace_not_ready 的提前返回补齐了 `next_operation_allowed:false`，与其他阻塞分支保持一致。此项不再留为待处理建议。

建议顺序：本轮确定问题及补充边界已经关闭，可据当前快照和离线回归记录审阅修复，再按主控既定计划进入下一轮导出性能工作；真实业务端到端及长期运行另行安排。本轮不扩大到导出性能改造。

未验证项：修复后的真实浏览器/MCP/DB 端到端、真实磁盘满或文件锁、真实 native wait 异常、真实 Agent 清理异常、真实断线后的迟到回调、长期运行和资源占用，均未执行。当前没有证据推翻旧成功样本，也没有证据把本轮离线通过扩大为长期稳定性结论。

最终审核文件 SHA-256（后续工作区变化需按新哈希重新核对）：

```text
35e583016b629ec88beb4f043019396aa7600c381d46a9bdd3692f9b8d4f9249  assets/resource/pipeline/PSIDE/create_record.json
591560442005ba7af6e1e6d7a116b241a60a39965e23ab678338ee576835d289  psauto/psauto/objects/service.py
612a0d6bfa8bd820a838348c29bf5d3170a5acf69544f0ab3fde49b2eb87b064  psauto/psauto/evidence.py
5bf30c98af351d03cfed3872a5b4da60617d0f87d38e64cf25837e3d7cd19ddf  psauto/psauto/recovery.py
1ff26523e35624c4b93e619c10193de1436747c44a9c17d7af3bfbeaa0d96645  psauto/recover_session.py
c2752715e8f549252bda911ea219a17f81b3b6f4f002ac557c0285cec332d1af  psauto/tests/test_object_service.py
f2140692ef7f092bcdd30d95cc6092172acc8a103e015d343125d85828a48042  psauto/tests/test_image_recognition.py
dc2d1de5f355674966c6f465761d1c56e34e763004a24617bb399ac5370c55bb  psauto/tests/test_recovery_cleanup.py
a167d85ea75d6769a5857799f0d4145fe2eb98caec69c21f4352b0e59edcd426  psauto/tests/fixtures/vision/build_success_feedback.png
```

回传目标为 `ps:0.0`。已核对本机 Cygwin tmux，目标 pane 实际为 shell；仅使用 display-message 通知，不把自然语言作为 shell 命令提交。通知本身不代表主控已读全文，主控按约定主动读取本文件。
