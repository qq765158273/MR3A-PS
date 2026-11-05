2026-11-05，pshelp 回复主控 ps：证据导出优化独立只读复核。

首次最终快照核对时间：2026-11-05 09:26:54 UTC（17:26:54 +08:00）。收到主控后续补充后，又将新增服务测试纳入范围；报告现列出的 18 个源码/文档/指标文件均已与实际 SHA-256 核对一致。

本轮为 `export-review-722d2ac-worktree-20261105`。仓库 `C:/Users/t-wangsen05/Desktop/MR3A-PS`，origin [qq765158273/MR3A-PS](https://github.com/qq765158273/MR3A-PS)，分支 `feat/psauto-jumpserver`，基线/当前 HEAD 为 `722d2acf1ff8f500479622fa94403cf3227c66f0`。审核目标是本轮尚未提交的五个代码/测试文件（包含主控补充授权的 test_object_service.py）及随后形成的性能文档，以末尾 SHA-256 标识版本。主控随后补充的真实运行记录仅作现有证据核对，执行方明确为主控。没有把此前针对 `548a63e` 的审核或历史成功调用冒充本轮结果。

结论：**本轮最终快照在源码、离线证据和独立内存验证范围内通过，未发现尚未解决的确定问题。没有发现证据遗漏、像素错误、逐节点引用保留或业务事实隔离回归；审核中发现的 benchmark P3 采样故障检测缺口已补齐并独立复验。** 已有 208 节点结果主要证明导出期新增私有内存明显降低；仅单次测量，耗时改善约 10.1%，不能推导整个业务流程或稳定平均收益。

本次复用当前 agent，没有另起 agent。只读源码和本机已有证据；使用实际源码 AST、内存路径、BytesIO 和模拟 owner/task/job 验证，没有导入或启动业务浏览器、操作桌面、连接数据库、创建 PS 对象、改源码、执行 commit，也没有重新运行会写资源/输出的 native benchmark 或完整套件。只写本报告。原有用户文件、前轮报告未修改。已确认 `ps:0.0` 实际为 shell，仅用 display-message 通知，不输入自然语言命令；通知不代表主控已读全文。

**审核中发现的 P3，最终已关闭：采样线程失败曾不能使 benchmark 测量失效。** 位置：[evidence_export.py:52](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/benchmarks/evidence_export.py:52)，最终故障传递位于第 143 行。中间快照的 `sample()` 在线程中直接调用 `memory()`；如果 GetProcessMemoryInfo 某次查询抛 OSError，线程退出并交给 threading.excepthook，主线程 `sampler.join()` 不传播异常，随后仍可能写正常的 `benchmark.json`。如果峰值发生在采样线程退出之后且结束前释放，数据可能低估峰值。

独立复现中间缺口时，从实际 benchmark 提取 `sample` 函数，以内存替身令 memory 抛 `OSError('injected sampler query failure')`，普通线程 join 未抛错，peaks 保持初始值。没有调用 Windows 内存 API 或修改 benchmark，也没有据此认定已有测量无效。

最终修复增加 sample_errors，采样线程捕获查询异常，main 在 join 和关闭 trace 之后检查该列表，出错时抛 `RuntimeError('Memory sampling failed; no benchmark metrics published')`，不会发布指标。独立提取最终 `main/sample/stable` 实际源码，用内存资源/native 替身及真实 Python 线程，在第二次内存查询注入异常（导出前和结束点查询正常），确认主线程收到明确错误、trace 关闭一次，且没有写出输出根目录的 benchmark.json。最终 benchmark SHA 为 `22d42e72ae1b752b9ab7bb120c49e892fa7fba01f9bff62224b01c0c7d286ebd`。因此此项不再是未解决问题。有效样本数量和查询时间戳仍可作为后续复现信息改进；现有 6 GiB 保护仍只针对当前 benchmark 进程。

核心实现核对：

- [evidence.py:263](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/psauto/evidence.py:263) 仅通过公开 `TaskDetail.node_id_list`、owner.get_node_detail 顺序读取节点。`_node_record` 返回名称、完成状态、识别/动作纯 metadata 和图片路径，截图缓存只保留 digest、reco_id、文件名；正常循环在下一次公开读取前 `del node`，不把 raw/draw 放入 report。对本机 Maa 绑定复查，get_node_detail 本身没有 Python 节点列表缓存。显式 tasker 或 trace.tasker 均可提供 owner；无 owner 的旧路径保留，并明确标注 `eager_compatibility`。
- [evidence.py:103](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/psauto/evidence.py:103) 的候选详情仍覆盖失败与嵌套事件，保持 reco_id 去重及截图映射；保存后释放 raw/reco，因此候选 draw_images 也不跨次保留。原生事件列表和顺序仍完整写出。弱引用内存验证检查了每次节点/候选读取前上一批 raw/draw 已释放，且禁止整批 `.nodes` 属性访问。
- [evidence.py:54](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/psauto/evidence.py:54) 对 C-contiguous 数组直接取 buffer 哈希；其他布局先作 C 顺序副本，与原 tobytes 的像素顺序一致。Pillow BGR raw decoder 产生的 RGB 与原反向通道切片一致。独立覆盖 **8 种 uint8 BGR 布局**：普通连续、水平反向、垂直反向、跨步采样、转置、Fortran 顺序、广播步长和反向通道视图；逐像素正确，视图与同内容连续副本也能去重。正常控制器输入为 uint8 H×W×3；未将结论扩大到任意 dtype/通道数。
- PNG 保持 `compress_level=1` 和无损编码，BytesIO 仅用来分开测量编码与写盘；frames/reco 缓存仍在写盘成功之后更新，没有发现写盘失败后错误地记为已保存的路径。原始 draw 图此前就未写成独立证据文件，本轮释放 draw 不属于删证据。
- 缺失 node 会明确抛 RuntimeError，没有静默跳过；profile 的 finally 仍完成统计。将本轮实际 exporter 接入本轮实际 `ObjectService` 的内存替身后，分别注入缺失节点、PNG 写入、report.json、events.json、summary.json 故障，业务 `saved/closed` 事实保持，evidence 为 failed，next_operation_allowed 为 false，第二次调用为 evidence_unavailable；每类只提交 1 次业务，sink 和 client 均清理 1 次。正常对照可继续。共 **6 类组合，0 不一致、0 异常覆盖返回**。
- service 相对基线仅增加 export_profile 字典、传入 profile 和写入 timings.evidence_export。将这三处还原后源码与 `722d2ac` 完全一致，因此本轮没有修改业务终态、operation_stopped、证据阻塞或清理策略。上述故障注入验证了实际组合行为，而不只依赖该文本结论。

证据完整性的独立验证：

1. 从 Git 直接读取 `722d2ac` exporter，与当前 exporter 使用相同内存任务、事件和像素。样例覆盖同名重复节点、候选失败、失败动作、raw hit=false 但规则通过、嵌套任务事件、重复 reco_id 和相同像素去重。两者的 **report/events/summary 所有字段、图片路径集合和 RGB 像素全部一致**，新实现下一次读取前 raw/draw 均无存活弱引用。独立验证不依赖 benchmark 的 normalized.json 声明。
2. 对主控已生成的三个 208 节点 native 离线目录，重新读取实际 report/events/summary，并比较规范化内容；每组 **208 节点、1664 条事件、99 张 PNG**，内容一致。重新解码了三组共 297 个输出 PNG，重算全部 RGB SHA-256，均与各自 manifest 一致；三组 manifest 相等，PNG 文件字节也全部相等。发布在 docs/performance/export 的三份原始指标与本机 benchmark.json 副本一致。
3. 本轮 `_pipeline_spans`、`_node_timing`、`_attach_timings`、`_write_summary` 的 AST 与基线一致，原有按 task/node/reco ID 的计时和候选统计未变。normalization 明确只剔除 timing/elapsed_ms/pipeline_event_ms/phase_ms；不把三次不同 native 运行的时间字段强行要求一致。208 节点 benchmark 本身是统一 ColorMatch/DoNothing 成功链，没有失败候选；失败候选和嵌套任务保留由前述独立内存对照及已有 native retry/failed-action 测试支持，不能说 208 链直接覆盖了这些失败路径。

性能数据及口径：

| 同一 208 节点离线链 | 导出耗时 | 导出期 private 增量峰值 | 导出期 RSS 增量峰值 |
| --- | ---: | ---: | ---: |
| 722d2ac 原实现 | 24.88852 秒 | 2,610,806,784 B（2489.86 MiB） | 2,605,821,952 B（2485.11 MiB） |
| 原算法加分项计时 | 24.04624 秒 | 2,618,798,080 B（2497.48 MiB） | 2,613,202,944 B（2492.14 MiB） |
| 本轮逐节点导出 | 22.38012 秒 | 26,054,656 B（24.85 MiB） | 26,042,368 B（24.84 MiB） |

已核对本机 `out/evidence_original.py` 与 Git 基线一致（换行规范化后相同），其 exporter SHA 为 `612a0d6bfa8bd820a838348c29bf5d3170a5acf69544f0ab3fde49b2eb87b064`。`out/evidence_profile_baseline.py` 是保留 eager/tobytes/旧颜色转换的诊断版，额外增加分项计时及编码/写盘分离，不能冒充未修改的原实现。文档将这两者分开报告，口径正确。

三组都使用历史 Record `out/objects/20261105_140117_227126` 的同一批 1920×1080 PNG，经离线控制器送入同结构的 native 链；不是重放实际 Record UI 创建。脚本将任务创建放在测量前，PNG manifest 验证放在测量后，只计导出阶段。Windows 20ms 采样的是当前 Python 进程 WorkingSetSize/PrivateUsage，包含进程内 SDK 分配，不是 Chrome/整机总内存，也不是整个 native 任务创建阶段的峰值。短峰值可能漏采，数值应称观测峰值。没有证据据此承诺精确最大值或任意机器的占用。

原版到新版单次耗时差为约 **10.0785%**；计时 eager 到新版约 **6.9288%**。两种 baseline 的耗时差异已说明运行波动，不能据此作稳定平均或严格因果拆分。新增 private 峰值相对原版约下降 99.0%，是本轮更充分的收益证据。64 节点 pilot（7.10638 秒、新增 private 820,215,808 B）仅作预算参考，不与 208 节点混算。

本轮 `phases_ms` 的测量区间没有嵌套重复累计：node_detail 只包 SDK 读取，保存中的 hash/copy、转换、PNG 编码、PNG 写入分别计时，metadata 分段累积；未归属部分单列。已有两个 profile 的分项之和加未归属与 total 差 0.01ms，为各字段四舍五入误差。`timings.evidence_export_ms` 是外层总计时，`timings.evidence_export.total_ms` 是同一段的内层总计时，**二者不能相加**，也不能再加到 Maa pipeline 阶段重复计算。文档对此已有明确说明。

读取主控 `out/export_unit_tests.log` 的最终结果为 **109 项，52 通过、57 显式开关跳过**；其中 EvidenceTests 九项通过。最初交接的 108/51/57 是较早一次数量，不与最终结果累加。日志覆盖真实 native retry/failed action、weakref 释放、strided 颜色、缺节点、兼容调用及磁盘异常。它们是主控已运行的测试记录，本 agent 没有重跑该套件；本 agent 自己运行的内存验证和像素重算在上文单独列出。

主控补充授权后，已独立审查 [test_object_service.py:198](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/tests/test_object_service.py:198) 的新增测试。相对基线仅新增这一用例：模拟 exporter 向 profile 写入 streaming/节点数/分项后抛 OSError，再检查 profile 和外层 evidence_export_ms 仍写入 timings，saved/workspace_ready 保留、evidence failed、禁止后续操作且只提交一次任务。该用例与本轮性能分项的故障语义相符，本 agent 未重跑此写临时文件的测试；主控完整套件日志已经包含它。测试文件最终 SHA 为 `c0ab74ce97c7d558155f558a1bf5d699fcfd4d775fc2ff999ad6717fb89cecc2`。

benchmark 最终接口分派也已复查：[evidence_export.py:133](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/benchmarks/evidence_export.py:133) 使用 `inspect.signature(exporter.export_task_evidence).parameters` 检查是否支持 profile；不再依赖基线文件名。原始接口和本轮新增 profile 接口可以使用同一入口，最终 benchmark SHA 仍为 `22d42e72ae1b752b9ab7bb120c49e892fa7fba01f9bff62224b01c0c7d286ebd`。

文档审查：[evidence_export.md](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/docs/performance/evidence_export.md) 的实现说明、三组数据、分项、样本数、采样范围、单次测量限制及“不能宣称整条业务提速 10%”与证据一致。未发现把跳过项、历史对象或部分故障路径冒充本轮真实业务成功。建议后续测量记录 benchmark 文件 SHA、依赖版本、PID/启动参数与有效采样数，便于复现；目前指标主要记录 Python 和 exporter SHA，这属于复现信息改进，不能据此否定已有像素和元数据一致性检查。

主控后续补充的真实接入证据也已核对：文档引用的 `out/objects/20261105_171830_968491` 存在完整 request/report/events/summary/timings。GM_EXP_REC 返回 saved_and_closed、built、workspace_ready，证据 complete、允许下一操作；原始 summary 为 208 完成节点、228 识别候选、20 次正常未命中、0 scan retry/节点失败/动作失败。新 profile 明确为 streaming，208 次 node 读取、20 次 candidate 读取，228 张 raw 去重为 100 PNG；20 个失败候选事件都有截图引用。发布的请求/结果/summary/timings 与本机原始数据一致，208 行 CSV 的字段逐项与 report 相符，保存/Build/空白台/最终图四张图片也与原图字节一致。DBX 文档及索引结构化返回支持主控所述三 VALID 索引；本 agent 未重新查询数据库，不将文档审核称为独立 DB 验收。

这次主控真实完整调用为 230.34 秒、导出 27.56508 秒，高于历史 GM_OPT_REC 的 169.95867 秒和导出 23.54608 秒。原生事件时间 200.719 秒、动作后缓冲 36.044 秒，209 次截图传输累计 58.51704 秒、81 次点击累计 33.93187 秒，可与文档核对。其导出前的执行阶段就明显变慢，不能归因为事后导出逻辑；具体底层变慢原因仍未定位。当前文档诚实分开离线对照与真实现场样本，没有把该新真实调用声称为提速证据。本 agent 仅核对主控新记录，未操作业务浏览器或创建这个对象。

下一步优先级：本轮采样故障传递已补齐；后续按需要增加有效样本计数，重复同一负载、统一进程/计时口径确认时间波动。SDK 详情复制、PNG 编码和 SHA-256 是已有 profile 的主要剩余耗时，磁盘写入占比小，下一轮优化需据此安排，继续保留逐节点/候选全部证据。当前授权未要求修改实现，本 agent 未实施代码修改。

未验证：本 agent 没有真实浏览器、数据库或 MCP 端到端操作；没有重新执行 208 节点 benchmark、真实磁盘满、真实采样 API 故障、不同 SDK/Pillow/NumPy 版本、多机器或长期运行测试。主控新真实样本不能证明整个业务调用端到端提速，离线数据也未证明整个进程/整机峰值都下降 99%。这些限制不影响本轮限定范围内的正确性结论。

最终审核文件 SHA-256：

```text
120232856f741983aa3a6fdaf61ad34be9ca1783a76d9fa121ed60a87e6dc1a7  psauto/psauto/evidence.py
c063323f1bed804753769c007abde0d1723eadc398675ed1a776fc987fe9baba  psauto/psauto/objects/service.py
012b78bd2e488234a2042ca0b719847e6f9d26e271b4bf17ba390f0e7c9fc353  psauto/tests/test_evidence.py
c0ab74ce97c7d558155f558a1bf5d699fcfd4d775fc2ff999ad6717fb89cecc2  psauto/tests/test_object_service.py
22d42e72ae1b752b9ab7bb120c49e892fa7fba01f9bff62224b01c0c7d286ebd  psauto/benchmarks/evidence_export.py
e9a722b288c5650366a1fc743dc3118d02d77afe18329207e3fe7836e21f2683  psauto/docs/performance/evidence_export.md
be0a7885f54c44b88e0958272dea5256f285de1da8349664c3220b76e3863d72  psauto/docs/performance/export/comparison.json
a073126e44c0630972bbf707cb795ab66ec5b96432557a660ba3c4ad2d7db4fb  psauto/docs/performance/export/export_baseline_208.json
30d7fc75e91b6a7680eb0f59709ecab2d7aaad45e59ec77a2108227ef332ab9b  psauto/docs/performance/export/export_original_208.json
ee38d967fe361e4f9ff88b799a8b166fe095f5b9580be220e41fb31deb4645de  psauto/docs/performance/export/export_stream_208.json
88a554d9a2487120cc6189e5d7669e1b20afd7715f9626b827aa6639f32de869  psauto/docs/performance/export/export_live_nodes.csv
fb14522f5ae6b036b527c42f85b41637eb2d9c4a99617af72187d744c6dc1dd2  psauto/docs/performance/export/export_live_request.json
8ba5c51cadee6a4645cfb2d2543744c84b3bb4995fc9196b4198e83cc44ba638  psauto/docs/performance/export/export_live_result.json
6ab1c1b8d88ce0b0ceb305b6af6003a28c51650c04a3b50d7dbf9addac153de5  psauto/docs/performance/export/export_live_summary.json
116504527ec80a45172cccdfde1258d3527e61c3233204e9ca6cc50ca58ec1a5  psauto/docs/performance/export/export_live_timings.json
ac8ccb8a192108b8c0e6e592b7bcf5b8398cab11f8547895ae4fdd31ff38985b  psauto/docs/images/acceptance-export-20261105/README.md
62393c76e224dfd635e194d401c1dc705f4b0f5914564db19d9ed182ab4fa2f1  psauto/docs/images/acceptance-export-20261105/dbx.md
497d2e4592dc94cdf5fef7ee56e56cad754f4c36522f7e9c48cccf7baa513a48  psauto/docs/images/acceptance-export-20261105/dbx_indexes.json
```

正式回复目标 `ps:0.0`；报告先保存，再发 tmux 通知，主控按约定主动读取。
