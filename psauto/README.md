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

空闲超时恢复、真实退出再进入命令、每个节点的 OCR/延迟/点击/失败检查，以及 GM 测试对象的截图见 [开发记录](docs/recovery.md)。`run_pipeline.py` 现在在业务任务开始前连接失败时尝试已识别的恢复路径，可用 `--no-recovery` 关闭；不会自动重放失败的业务任务。每次任务的 Maa 原生截图、识别和动作事件保存到本机 `out/runs/`，恢复证据位于 `out/recovery/`。

```powershell
$env:PSAUTO_TEST_BROWSER_CHANNEL = 'chrome'
$env:PSAUTO_TEST_OCR = '1'
$env:PSAUTO_TEST_CLI = '1'
& $python -m unittest discover -s tests -v
```

测试使用本机临时 HTTP 页面和临时资源，不连接 JumpServer。未设置 `PSAUTO_TEST_BROWSER_CHANNEL` 时跳过浏览器集成测试；未设置 `PSAUTO_TEST_OCR` 时跳过 OCR 模型测试。
