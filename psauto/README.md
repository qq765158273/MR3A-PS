# psauto

在 JumpServer 的 Web 远程桌面中，通过 Playwright CLI 获取画面和发送输入，复用 MR3A 的 MaaFramework、原 AgentServer、资源和 Pipeline。仅针对 dev/test 环境使用。HRDEV 中已实际验证截图、坐标点击、组合键、英文输入及最小 Pipeline；真实中文输入、CLI 会话恢复及长期无人值守运行仍须验证。

## 环境

需要 Windows、Python 3.11 x64、Node.js、Playwright CLI 和已安装的 Google Chrome。示例配置的 `connection_mode` 是 `cli`：Python 复用已授权的 CLI 会话，不启动新浏览器，也不要求再次登录。CLI 会话和 Chrome 扩展连接须持续有效。

在已安装 Python 3.11 的机器上，从本目录执行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$python = '.\.venv\Scripts\python.exe'
```

本次开发机没有系统 Python，已在仓库的 `.psauto-runtime/` 下创建隔离环境；在本目录可使用：

```powershell
$python = '..\.psauto-runtime\venv\Scripts\python.exe'
```

本机加载 MaaFramework 时曾因系统 `MSVCP140.dll` 初始化失败而出现 `WinError 1114`。当前隔离 Python 目录中放置了已安装的 NumPy 包内的微软签名运行库用于测试，没有替换系统 DLL。其他环境出现相同错误时，需要检查 Windows 应用程序日志和 Microsoft Visual C++ 运行库版本。

## 连接与探测

只在没有配置文件时复制示例，避免覆盖已有设置：

```powershell
Copy-Item config.example.json config.json
```

在 `config.json` 配置 `cli_session`、`cli_script`、`cli_workdir`、`display_frame` 和 `display_selector`。其中 `cli_script` 应指向**启动该会话时使用的同一份 CLI**；本机现有会话由 npm 缓存中的 CLI 创建，所以本地配置指向那份缓存，而非新安装的副本。

```powershell
& $python runner.py probe
```

`probe` 直接使用已连接的会话。`login` 和 `discover` 属于早期独立浏览器模式，当前 CLI 方式不需要执行。CLI 会话失效时须重新连接并授权，自动重连还没有实现。

配置中的登录态、资源目录及相对输出路径均相对于配置文件所在目录解析，避免从其他工作目录运行时把敏感文件写到仓库根目录。

当前现场观察到的 frame 为 `iframe[src*="/lion/connect"]`，画面元素为 `#display`。不要把连接地址中的临时参数写入示例或提交。

`probe` 在 0、3、10 秒截图至 `out/`，重复执行会覆盖这三张图片。示例配置采用 `native_canvas` 和 `1920×1080` 基准：读取原始 canvas 并裁掉 Guacamole 缓冲区填充，不以缩小后的浏览器截图做识别。每次截图及操作前检查逻辑分辨率；出现多层 canvas、分辨率不符、不可见或不支持的变换时失败，不自动点击。坐标换算已在本地模拟页面及真实 JumpServer 上验证，仍需针对其他画面与环境继续验证。

只读测量中，JumpServer 画布曾是 `1920×1088`，其父元素逻辑尺寸为 `1920×1080`，因此截图裁掉底部 8 行。浏览器显示可能是缩小的，点击时会按实时画布尺寸换算；坐标被裁剪、遮挡或位于视口外时拒绝点击。画布结构变化时不要强行绕过检查，应重新测量适配。`viewport` 模式保留原来的网页元素截图方式，不适用于本项目的固定原始像素坐标。

CLI 默认 `canvas_refresh_mode:guacamole`：读取原图前调用远程桌面现有 Display.flush 排空浏览器已接收的绘图队列，最多等 5 秒；组件/API 缺失、尺寸不符或断线即停止。它不能请求或保证远端新帧，任务仍等待下一状态的识别。`browser` 模式显式保留原浏览器截图刷新供兼容诊断，不自动回退。剪贴板网页抽屉仍需浏览器动画刷新及隐藏检查，最后粘贴前再确认连接。五次测量中原图读取编码约 47–50ms，完整 CLI 请求约 932–1001ms；分项及完整 Field/AE 验收见 [Pipeline 复核](docs/performance/pipeline_audit.md)。

后续已用项目 [官方 CLI 配置](playwright-cli.config.json) 将 settle 设为 0，截图含解码降至约 180ms，并完成 Field / Date / Record＋Build / 四步 AE 的连续完整 MCP 与 DBX 验收。`config.example.json` 使用 `cli_session:psauto-fast`、`cli_settle_ms:0` 和常驻客户端；每次客户端启动会查询实际 settle，不符就停止，不提交浏览器动作。配置更改只在 CLI daemon 启动时生效。

本机可复用已授权浏览器，在配置的 cli_workdir 中，用与原会话相同的 CLI 安装执行：

```text
node <cli_script> -s=psauto-fast attach psauto-discovery --config=<绝对路径>/psauto/playwright-cli.config.json
```

`psauto-discovery` 为本机现有已绑定浏览器；保留其运行，由新的 psauto-fast 会话加载官方配置，避免重新走扩展授权。已配置浏览器处于空白操作台时再调整连接。`cli_settle_ms:null` 兼容旧会话；非 null 的校验需要 `cli_persistent_client:true`。完整数据、证据及边界见 [0ms 配置验收](docs/performance/settle_optimization.md)。

修改代码或 config.json 后，重新启动既有 MCP 连接以加载变更；本轮完整验收使用的是新启动的最终配置服务实例。

画面和安全点击位置确认后，可使用 `capture` 做进一步验证：

```powershell
& $python runner.py capture
& $python runner.py capture --click X,Y --out out/click.png
& $python runner.py capture --combo Control+o --out out/combo.png
```

将 `X,Y` 换成截图中的安全坐标。键盘输入取决于远程桌面的焦点，中文输入、断线重连以及锁屏或断开 RDP 后的行为均需单独实测。

浏览器操作在执行中超时时，会话会拒绝后续请求并取消尚未执行的排队操作。已经发给浏览器的操作可能仍在运行，不能保证撤销；必须先检查远程界面状态，再启动新会话。

## Maa 流水线

使用 MR3A 自带的资源包和 OCR 模型。在 `psauto` 目录执行原项目的资源准备脚本：

```powershell
& $python ..\tools\ci\configure.py
```

PSIDE 节点位于原 MR3A 资源目录 `assets/resource/pipeline/PSIDE/`。运行时加载原资源包，启动原 `agent/main.py` 的 AgentServer 并通过 Maa AgentClient 绑定其已有组件：

```powershell
& $python run_pipeline.py <entry>
```

`PSIDE_WindowReady` 是只读检查节点，使用 Maa 内置 OCR 和 `And` 检查标题中的 `Applica` 与 `HRDEV`。`PSIDE_Demo` 使用 Maa 内置的 `KeyDown`、`ClickKey`、`KeyUp`、OCR 和模板匹配，完成 `Ctrl+O` → 识别“打开定义” → 点击“取消”；2026-11-03 已在 HRDEV 完整验证并返回主窗口。对话框不存在时取消流程失败；按键失败时控制器会尽力释放已按下的键，但若连接已断开不能保证释放成功。另已在名称输入框测试英文输入并取消，未执行搜索或保存。

这些节点及“取消”模板基于当前 HRDEV、中文对话框和 `1920×1080` 画面，不应直接用于其他环境。节点显式覆盖 MR3A 的默认 `on_error`，避免未识别到目标时走通用回退并误报成功。输入编码和不同版本界面仍须现场验证。

自定义控制器仅替代截图和输入通道，不改造 OCR 或 Pipeline 引擎。现有 `assets/interface.json` 仍使用 ADB，当前通过 Python 入口接入 CLI，尚未修改 MR3A GUI 的控制器选择。

`config.json`、`state/`、`out/`、`debug/` 及复制的 OCR 模型已被 Git 忽略。登录态和截图可能包含敏感数据。

## 测试

`mcp_server.py` 对外提供 `create_field`、`create_record`、`create_ae`。三个操作均在保存并关闭、返回空白操作台后结束，不重新打开对象，不核对已保存内容；内容交由 DB 验证。`success: true` 和 `status: saved_and_closed` 仅代表界面操作完成。`workspace_ready: false` 表示操作台尚未释放，该服务实例会阻止下一对象进入；检查操作台后重启服务。固定 UI 步骤位于 `assets/resource/pipeline/PSIDE/create_*.json`，Python 只绑定参数及调用 Maa。Record 字段可传名称字符串，或 `{name, key, alternate_search_key, listbox, search_key}`；普通 Search Key 要求 Key，非 Key 使用 Alternate Search Key。SQL Table 可传 `build: true`，表空间参数 `tablespace` 在当前 HRDEV 默认为 `HRAPP`。Build 只创建当前定义及其索引，使用 Skip existing，成功反馈后关闭。完整调用的实测进度见 [dbx 验收记录](docs/acceptance.md)。

返回结果将业务与证据分开：`evidence_status` 为 complete/partial/failed，异常阶段在 `evidence_errors`；业务执行/退出异常另有 `operation_error`。已经保存关闭时，写盘故障仍保留 `saved:true`、`workspace_ready:true`，同时 `next_operation_allowed:false`，服务阻止后续业务。调用方需要同时读取这个字段，排查故障并重启 MCP 连接后再继续，不重放已完成任务。对应阻塞状态为 evidence_unavailable / operation_stopped；原有工作台和不确定会话保护保留。详见 [审核修复与验证](docs/reliability_fixes.md)。

运行 MCP 服务（从 `psauto/` 目录）：

```powershell
..\.psauto-runtime\venv\Scripts\python.exe mcp_server.py --config config.json
```

这是 stdio MCP 服务，由 MCP 客户端启动和传参。`call_mcp.py` 是开发验收客户端，`out/` 下的参数文件只是某次调用的请求数据，不是业务 Pipeline，也不会提交到 Git。正式调用直接传 MCP 工具参数。

CLI 输入适配器默认保持一个客户端进程，调用配置指定安装中的官方 Playwright CLI `Session.run`；`cli_persistent_client:false` 可用于原单次启动方式的诊断对照。每个 MCP 运行目录新增 `timings.json`，记录 Pipeline、证据导出和无入参内容的控制器请求耗时。重复截图共用文件路径，每个节点和识别事件仍保留自己的判决与截图引用。组合键编码和性能验证见 [执行链路优化](docs/performance/optimization.md)。

每次运行还会自动生成 `summary.json`，由 Maa 原生 `ContextEventSink` 的 `Node.*` 事件汇总节点数、识别/动作失败、阶段耗时、动作类型和识别算法；`report.json` 的每个节点包含识别、动作和总耗时。性能分析使用这些运行证据，不依赖人工估算。

汇总用原生 `task_id/node_id/reco_id` 对应节点，识别重试、同名节点重复执行和嵌套任务分别统计。`candidate_misses` 是候选未命中，`scan_retries` 是额外识别轮次，实际任务/节点/动作失败分别看 `succeeded`、`pipeline_node_failures`、`action_failures`；旧字段 `recognition_failures` 仅保留为候选未命中的兼容别名。原始 `hit:false` 也可能是正确的反向识别，节点的 `recognition.rule_passed` 表示 Maa 是否判定规则通过。

`report.json` 的 `timing.total_ms` 是原生节点从开始到完成/失败的时间，包含该节点取图准备及全部识别重试；`phase_ms.scan_prepare_ms` 包含截图、扫描间隔及其他扫描准备，不能等同于单独的截图回调时间。`timing_complete` 说明所有报告节点是否都取得了完整计时，`unattributed_ms` 明示事件跨度内尚未分配给节点的时间；各阶段与未分配时间之和等于 `pipeline_event_ms`。截图文件数在导出时统计，不含之后保存的最终 `after.png`。

`create_ae` 接收 1–4 个 `steps`，各项为 `{type: "SQL" | "PeopleCode", code: "..."}`，在 MAIN 下依次生成 Step01–Step04。代码通过 JumpServer 剪贴板输入，再识别保存反馈，最后关闭所有本次编辑窗口；不执行 AE。两步和四步已完整实测并通过 DBX 内容验收。各卡点的 ROI、图片/OCR 选择、延迟、有限重试与下一步条件见 [判决表](docs/recognition_decisions.md)。

空闲超时恢复、真实退出再进入命令、每个节点的 OCR/延迟/点击/失败检查，以及 GM 测试对象的截图见 [开发记录](docs/recovery.md)。`run_pipeline.py` 现在在业务任务开始前连接失败时尝试已识别的恢复路径，可用 `--no-recovery` 关闭；不会自动重放失败的业务任务。每次任务的 Maa 原生截图、识别和动作事件保存到本机 `out/runs/`，恢复证据位于 `out/recovery/`。

```powershell
$env:PSAUTO_TEST_BROWSER_CHANNEL = 'chrome'
$env:PSAUTO_TEST_OCR = '1'
$env:PSAUTO_TEST_CLI = '1'
& $python -m unittest discover -s tests -v
```

测试使用本机临时 HTTP 页面和临时资源，不连接 JumpServer。未设置 `PSAUTO_TEST_BROWSER_CHANNEL` 时跳过浏览器集成测试；未设置 `PSAUTO_TEST_OCR` 时跳过 OCR 模型测试。
