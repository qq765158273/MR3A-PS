2026-11-05，pshelp 回复主控 ps：`roundtrip-batching-66196b3` 独立只读审核。

最终快照核对时间：2026-11-05 09:34 UTC（17:34 +08:00）。仓库 `C:/Users/t-wangsen05/Desktop/MR3A-PS`，origin [qq765158273/MR3A-PS](https://github.com/qq765158273/MR3A-PS)，分支 `feat/psauto-jumpserver`，基线 HEAD `66196b32fed5d31925b136d7b4d1bb40792f0e74`。范围是 cli_controller、两组相关测试、transport benchmark 及其性能文档/roundtrip 数据；用户未提交的其他文件不在范围内。没有重审上一轮导出，也没有启动业务浏览器、数据库、MCP 创建对象、修改源码或提交。

结论：**本轮合并浏览器检查的实现和隔离对照在限定的只读/离线范围内通过，未发现确定的保护回归。** 每个请求仍重新读取连接、尺寸、画布和焦点；超时后的迟到 flush 回调不会继续 focus、键盘、点击或粘贴；响应解包、decoder 计时和旧动作尾部保持兼容。隔离数据支持本地测试页面的往返减少，但不支持真实 RDP 业务提速结论。现场 A/B 当前因 RDP 关闭及账号页未恢复而未完成，主控继续处理即可，不是本轮审核阻塞项。

方法：读取 `66196b3..工作区` diff、源码和测试日志；重算 isolated JSON 的 SHA、baseline/current 源码 SHA、交替顺序、样本数、median/p95/max 和 capture_cli+decode 分项；用 Node 内存页面替身执行合并后的实际 JS；用 Python 内存替身执行 `PlaywrightCliSession.request` 的响应解包/decoder 故障；用 AST 比较动作尾部与基线。没有等待真实浏览器，也没有使用现场输入。

源码/数据 SHA：

```text
da06412fa23f3482cb334b9ab08bba1bd327d912a4466b71e8f1a513e7aef775  psauto/psauto/cli_controller.py
a0f1b656e4462e112cf50879ce7a1cdd8e198a1235dc7b037c3eef6b6ffa88ab  psauto/tests/test_cli_transport.py
e17f2b49a20bb4892daccd49e2944d97031e465a78bf0427ff8b49adf9eb43fd  psauto/tests/test_jump_clipboard.py
469e10ba2efb92849a8059ea61bba0051b236e645ac6951e29198305dd7f155d  psauto/benchmarks/transport_roundtrips.py
1f2e7e8f76c69a64ddecefc90ca3848a89b27e180bdd98ddb7daf4a6e1b7da2d  psauto/docs/performance/transport_roundtrips.md
689efea89a52f15be8fd3f624dc5ba6047c4fcb19fe0843ce34414da784d7803  psauto/docs/performance/roundtrips/isolated_comparison.json
7f1782bc88cc26ba8ba6d249e5a5ee8e8b2677c2a575baa30dedf5f22edeaf88  psauto/docs/performance/roundtrips/prechange_live_probe.json
ca83533ce97c7f343a1b1edca7c2df49faa972eb0d3b1634dd3183c7e5eb9854  psauto/docs/performance/roundtrips/live_readonly_comparison.json
5a9738dc963489f0dced9eb49448c326db4a24eada91af607ec2e3f96459847f  baseline 66196b3 cli_controller.py
4d5662de76fe443a9d86c797902db44c90b3f0e7159b663955ee5a15b9e0073b  baseline 66196b3 cli_worker.cjs
```

合并实现核对：

- [cli_controller.py:242](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/psauto/cli_controller.py:242) 的 `readState` 在每次需要时重新通过单次 `evaluateAll` 读取 transport、连接状态、必要 flush、`_INSPECT`、尺寸和键盘焦点。没有跨请求缓存。缺 canvas、组件/API、隧道关闭、stale Connected、错误尺寸、非法 buffer、隐藏/变换、失焦均在输入前抛错。
- flush 的 Promise.race 超时仍位于页面外；页面内回调只读取状态、flush 和 inspect，成功返回后才进入 point/key/input 分支。迟到 callback 不持有输入闭包，也不会执行 focus、key、click 或 Ctrl+V。
- browser 刷新模式保留独立的只读截图/动画刷新，再次 readState；Guacamole 模式只 flush。点击坐标、canvas/iframe 遮挡和 swipe 逐步尺寸检查与 `66196b3` 动作尾部 AST 相同（仅最终返回从 `true` 包成 value/timing）。key_up 仍可直接释放，不要求 canvas 状态通过，以保留异常清理路径。
- Python [cli_controller.py:50](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/psauto/cli_controller.py:50) 解包 `{value,timing}`。无 decoder 时返回原值，decoder 只包 Python 解码；`elapsed_ms` 计 CLI response 往返，`decode_ms` 独立写入。decoder 抛错时保留一行 transport timing，不重发请求、不把像素正文写入 timing。传输失败同样只写一条 elapsed 行，不调用 decoder。
- service/controller 调用已显式为 screencap 传 decoder；旧的 `request` 调用返回 bool/dict 的路径仍可用。新增字段 body/browser roundtrip/validation/flush/inspect 具有嵌套关系：不能直接相加，也不能把 decode 加回 elapsed。

内存/离线复验结果：

- Node 内存页面替身覆盖 **16 类**拒绝场景：缺 root、缺组件、closed tunnel、stale label、clipboard 不可用、错误尺寸、small buffer、hidden、bad transform、extra layers、失焦、缺 flush API、flush 错尺寸、flush 抛错、flush 断线、点击遮挡；均无 key/click。
- late flush 场景让页面外 race 超时后手动触发延迟回调，确认没有 focus、key 或 click。正常 screencap 只执行一次 flush/一次 probe；失焦或尺寸变化发生在上一请求成功后，下一 key 请求仍重新检查并拒绝。
- browser 模式 screenshot retry 仍最多只重读只读截图；截图刷新中断线时 prepare 不 focus。key_up 清理可绕过画布状态，未改变既有释放语义。
- Python 内存复验覆盖 response value 为 true/false/dict、decoder 抛错、transport 抛错。decoder 抛错得到 `elapsed_ms=10, body_ms=3, browser_roundtrip_ms=2, decode_ms=14` 的单行 profile；没有 payload、没有重复 elapsed、没有 decoder 重放。

测试日志：

- CLI 集成日志 `batch_cli_tests.log`：9 项，8 通过、1 个可选 OCR 跳过；末尾的配置检查、key release、截图/点击和只读重试均通过。
- clipboard/Guac 日志 `batch_clipboard_tests_final.log`：10 项全部通过，覆盖组件/API 缺失、flush 异常/超时、迟到回调、抽屉动画、粘贴前断线和新增失焦/改尺寸拒绝。
- 普通日志 `batch_unit_tests_final.log`：111 项，53 通过、58 显式跳过；不把跳过项算通过。新增 decoder timing 用例和其他测试均在日志中。

隔离对照复核：

`isolated_comparison.json` 的 baseline SHA 与 `git show 66196b3` 的 cli_controller/worker 重算一致，current SHA 与当前 cli_controller 一致；12 轮每实现 12 样本，顺序按轮交替，settle 预期/实际均为 0。统计和原始 measurements 可重算，24 次异步像素修订、24 次 click、2 次 clipboard 的 state 为 `revision:24, clicks:24, pastes:2`，没有重复输入或旧像素通过。

| 指标中位数 | baseline | current | 观测减少 |
| --- | ---: | ---: | ---: |
| inspect | 32.1666 ms | 14.7921 ms | 54.0% |
| screenshot CLI | 64.3298 ms | 44.9018 ms | 30.2% |
| screenshot 含 decode | 107.0108 ms | 88.0691 ms | 17.7% |
| key | 43.0748 ms | 27.0900 ms | 37.1% |
| click | 70.6422 ms | 54.2662 ms | 23.2% |

这些是同一本地页面、同一官方 CLI、独立会话、单次 12+12 轮交替样本；不能替代现场隐藏 Chrome/RDP。`prechange_live_probe.json` 只有本轮开始的 12 次只读现场分解，显示页面 visible、1920×897、原图 1920×1080、decode 约 43.7ms、截图 CLI 约 124.4ms；它不是 baseline/current 对照。现场 `live_readonly_comparison.json` 已补齐 12 对只读截图 A/B，仍不代表真实业务输入；真实业务 A/B/验收另行处理。

已有 GM_EXP_REC 慢于 GM_OPT_REC 的历史差异仍不能归因到本轮：前者原生执行约 200.7s、后者约 144.7s，主要新增截图/输入，发生于不同时间。当前隔离收益只证明本地 transport 往返的观测改善，不能证明系统底层 CPU/CDP/网络原因或真实业务端到端提速。

未发现确定问题。限制和未验证项：真实 RDP 恢复、真实隐藏页面长尾、现场 A/B、长期运行、不同 Playwright/Chrome/Guacamole 版本以及最终 MCP 业务验收均未执行；主控正在处理账号页/登录状态，不等待也不操作它。该范围外的真实验收不阻塞本轮只读审核。

最终结论：本轮合并查询、迟到回调保护、响应解包/decoder 计时、动作兼容和隔离对照在限定范围内通过；报告已写入指定路径，下面仅发送一次通知。

**最终补核附记（2026-11-05 10:05:38 UTC / 18:05:38 +08:00）：** 主控要求仅补核 Record ROI 修复和现场只读对照状态；没有重做本轮适配器全量审核，也没有操作浏览器、数据库或源码。

- `assets/resource/pipeline/PSIDE/create_record.json` 的 `R_AttrFocus.roi_offset` 已从 `[-5,20,100,400]` 改为 `[5,20,90,400]`。使用固定 anchor `[659,290,65,24]`，旧 ROI 为 `[654,310,165,424]`，新 ROI 为 `[664,310,155,424]`。新增 `test_image_recognition.py` 用真实 `record_selected_effdt_prefix.png` 复现旧 crop 失败，并验证五字段正例和 `EFFDT_X/EFFD/X_EFFDT` 反例；不放宽字段名正则。日志 `psauto/out/batch_native_vision_tests.log` 最终为 13 项通过、0 跳过。当前文件 SHA：`a963916f8f9ce23a6a3dd9e079afcb4fce9197f3c70aaf6ea87669677149d090`（JSON）、`8d938c3705a3fa5f76d849035bb0f3e0bb02d216f26db68e394c4f03cfc23a1b`（测试）、`e5ab5857c911c51a8c7d715721916b0e7bf52b6248449423d03f7ec5be6baad2`（fixture）。
- 主控提供的首个 `GM_RPC_REC` 失败证据目录 `psauto/out/objects/20261105_175023_339465` 已存在完整 report/events/summary/timings 和截图，任务在保存前停止，137 节点；该调用不计成功、不自动重放。主控随后用独立临时 Pipeline 丢弃未保存草稿并确认空白台，再从头启动 `GM_RPC_REC2`；本 agent 不等待、不操作该真实 MCP 运行，也不把其尚未完成状态计入审核。
- 现场只读 `live_readonly_comparison.json` 已更新，当前 SHA `ca83533ce97c7f343a1b1edca7c2df49faa972eb0d3b1634dd3183c7e5eb9854`。12 对 baseline/current 截图像素相等；页面 visible、1920×897、原图 1920×1080、settle 0。现场只读中位数为截图 CLI `180.5→76.7ms`，含 decode `227.4→123.7ms`，inspect `101.1→37.2ms`；这仍是只读截图对照，不是业务输入或端到端提速证据。此前“现场 A/B 未执行”的表述仅保留历史背景，现已修正为“现场只读截图 A/B 已完成，真实业务 A/B/验收仍未完成”。
- `transport_roundtrips.md` 当前 SHA 为 `9da23c4d8d38e641e643df6dcead775f6046fbeac3d89ab0e5d7bfcdfcc96da0`；此前报告正文表中的旧文档 SHA 已由本附记更正。上述现有适配器 SHA、isolated 数据 SHA 保持不变。主控补充的真实现场状态不改变本轮适配器保护结论，也不把 `GM_RPC_REC2` 的运行中状态当作审核通过。

**最终必要补核（2026-11-05 10:15:20 UTC / 18:15:20 +08:00）：** 主控补充了 Record Build 后关闭缺口；本 agent 只核对当前 JSON、fixture、测试和已有证据，不操作真实 MCP。

- 当前 `create_record.json` 的 `R_BuildFinished.next` 已为 `R_BuildCloseSaved`。该节点是 `And`：对象名 OCR 仍使用原 `__PARAM_name_regex__`，关闭按钮使用已有 `PSIDE/active_editor_close.png`、threshold `0.95`，`box_index:1` 选第二个识别框，`target_offset:[4,4,-8,-8]`，成功后直接到 `PSIDE_CreateRecord_SavedAndClosed`。`R_CloseSaved` 的非 Build 关闭路径仍存在且未改动。没有放宽名称正则；当前节点静态检查确认这一点。
- 新增 `record_build_before_close.png` 为 1920×1080 RGB；`record_selected_effdt_prefix.png` 也为 1920×1080 RGB。最终文件 SHA：`ede8d1589d58585d8a6a16ab07453c880230efed7445b2c0606bbe14fe5b4780`（create_record.json）、`3a2f7aa05fb11d9cfa4699055c7d77f9d57aabf1ef323a889986fbd47991ef16`（test_image_recognition.py）、`a8b08c40c19a929f69c19d3e5402f646e6d5da1f17b5d46f9e25eb6cd543c814`（record_build_before_close.png）、`e5ab5857c911c51a8c7d715721916b0e7bf52b6248449423d03f7ec5be6baad2`（record_selected_effdt_prefix.png）。
- 我在仓库外使用当前 Python/native Maa 离线运行新增的两个用例，实际结果 **2/2 通过**：旧 ROI crop 失败、新 ROI 五字段与错误字段名边界通过；Build 关闭节点正确名称只点关闭按钮框内一次，相似名称/缺失图标不点击。无浏览器、DB 或对象创建。主控提供的最新日志称原生识图 14 项全过；本机当前 `batch_native_vision_tests.log` 文件末尾仍显示 `Ran 13 tests`，因此本报告把 14 项作为主控日志声明，把 2 项作为本 agent 独立重跑，不将两种计数相加。该文件版本差异不改变两条新增用例的独立结果。
- `psauto/out/objects/20261105_180031_075459` 的原始 report/events 显示该调用仍走旧 `R_CloseSaved`，Build 已完成但 `PSIDE_CreateRecord_SavedAndClosed` 未命中，最后 `R_CloseSaved` pipeline failed；summary 为 207/208 完成、pipeline_node_failures=1、succeeded=false。这是补丁替换前的 `GM_RPC_REC2` 失败证据，不能用来验证新 `R_BuildCloseSaved` 已在真实 MCP 中成功。主控已明确该 partial 不计成功，随后 `GM_RPC_REC3` 从头运行；本 agent 不等待或操作它。
- 因此本次补核结论是：**当前关闭节点的静态结构和两个新增离线 native 用例通过；主控旧 partial 证据保留为失败样本，尚无本 agent 独立的真实新节点端到端成功证据。** 这不推翻本轮适配器保护结论，也不把保存/Build 完成等同于最终 Record 成功。

**最终主控验收收尾附记（2026-11-05 10:24:10 UTC / 18:24:10 +08:00）：** 主控已完成真实验收；以下全部是主控运行/DBX 证据，本 agent 未操作浏览器、MCP 或数据库，也不将其称为独立验收。

- `GM_RPC_REC3` 从头完成，工具返回 `saved_and_closed`、`built:true`、`workspace_ready:true`、`evidence_status:complete`、`next_operation_allowed:true`，耗时 173.22 秒，原生节点 207。文档说明有 24 次候选未命中，其中 4 次额外状态扫描；这些扫描不是重发输入，不能把该调用写成零扫描/零候选未命中。对应归档 [record3_result.json](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/docs/performance/roundtrips/record3_result.json)，证据目录为 `out/objects/20261105_180726_715320`。
- 随后同一新 MCP 实例连续完成 `GM_RPC_F1`（48.89 秒，40 节点）及引用它的 `GM_RPC_REC4`＋Build（175.53 秒，207 节点）。两次都返回 saved_and_closed、workspace_ready、evidence complete、允许下一操作；Record4 为 0 识别轮次重试、0 节点失败、0 动作失败。对应 [continuity_results.json](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/docs/performance/roundtrips/continuity_results.json)。
- 主控归档的 DBX 只读结果确认 REC3 的五字段 USEEDIT、HRAPP、3 个 VALID 索引和 0 行；连续实例确认 F1 类型 0/长度 11/标签和长短名称，以及 REC4 字段顺序/属性、HRAPP、3 个 VALID 索引和 0 行。证据入口为 [acceptance-roundtrips-20261105/README.md](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/docs/images/acceptance-roundtrips-20261105/README.md)。这些是主控提供的 DBX 结果，不是本 agent 独立数据库检查。
- 日志版本已澄清：最终原生识图日志是 `psauto/out/batch_native_vision_tests_final.log`，归档副本为 [verification_native_vision.txt](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/docs/performance/roundtrips/verification_native_vision.txt)，末尾为 **14 项通过**；旧 `batch_native_vision_tests.log` 的 13 项是过时文件。最新普通套件归档 [verification_unit.txt](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/docs/performance/roundtrips/verification_unit.txt) 为 **113 项、53 通过、60 显式跳过**。本 agent 没有重跑这两份最终日志，仅核对主控归档内容。
- 报告首页此前自填的 17:34 时间是笔误；首次落盘应记为 **17:54:42 +08:00**。本附记实际修订时间为 18:21:21 +08:00。此前所有独立复验和失败证据的历史时间保留，不改写成主控真实验收由本 agent 完成。

归档文件 SHA：`a2c910e66681672c37ea9a58c0c5669d5041f685b197215d17762ce1634d1268`（record3_result.json）、`60156500600811286bf49368e408d3f99225eadd0230c4c715cd49fd143ea456`（continuity_results.json）、`02d5f211a0d61731525986d43ffd42970d58befb1cfd1c4333477670e9b4586e`（verification_native_vision.txt，14 项）、`e5fcafda5ad4228f749f65ad2cc189c4072789d41f312e4ed4bcca8efe8229c3`（verification_unit.txt，113 项）、`ce1c2e6a08291aa7568e04ec61b205994da55bb28cfbc1a1909d83eb7852a88c`（acceptance-roundtrips README）。本 agent 未重跑或独立执行这些真实/DBX证据。

本轮最终状态：适配器合并检查与离线独立复验仍按原结论通过；Record ROI/Build 关闭修复由主控真实 MCP 进一步验收通过；两次失败样本仍保留并按失败/partial 统计；最终连续调用与 DBX 结果支持主控的业务验收结论，但不扩大为长期无人值守保证。
