# psauto

在 JumpServer 的 Web 远程桌面中，通过 Playwright 获取画面和发送输入，再由 MaaFramework 运行识别流水线。仅针对 dev/test 环境使用。当前只完成本地模拟页面的验证，JumpServer、RDP 和 PSIDE 的实际行为仍须现场验证。

## 环境

需要 Windows、Python 3.11 x64 和已安装的 Google Chrome。`config.example.json` 的 `browser_channel` 为 `chrome`，Playwright 会启动独立的临时浏览器配置，不会直接使用已打开的 Chrome 标签页或其登录状态。若要使用 Playwright 自带 Chromium，可将该值设为 `null` 并运行 `python -m playwright install chromium`。

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

在 `config.json` 填写 `jumpserver_url`，然后运行：

```powershell
& $python runner.py login
& $python runner.py discover
```

`login` 会打开浏览器供用户完成登录和 MFA，按回车后保存登录态。`discover` 中手动打开 dev/test 资产，看到远程桌面后按回车，检查输出的页面、frame、canvas 尺寸和父元素。输出 URL 可能带有临时凭据，不要直接公开。

配置中的登录态、资源目录及相对输出路径均相对于配置文件所在目录解析，避免从其他工作目录运行时把敏感文件写到仓库根目录。

根据实际页面填写 `connect_url`、`display_selector`，必要时填写 `display_frame` 和 `pre_connect_clicks`。画面元素应覆盖远程桌面所有图层。连接 URL 可能是一次性的；是否能够重用，以及登录态是否足以恢复会话，必须在目标环境验证。Playwright 的 storage state 不包含所有站点可能使用的会话信息，例如 `sessionStorage`。

```powershell
& $python runner.py probe
```

`probe` 在 0、3、10 秒截图至 `out/`，重复执行会覆盖这三张图片。检查截图是否完整、清晰，像素尺寸是否和画布实际尺寸一致。即使 `device_scale_factor=1`，RDP 或页面仍可能缩放，必须实际验证坐标。

画面和安全点击位置确认后，可使用 `capture` 做进一步验证：

```powershell
& $python runner.py capture
& $python runner.py capture --click X,Y --out out/click.png
& $python runner.py capture --combo Control+o --out out/combo.png
```

将 `X,Y` 换成截图中的安全坐标。键盘输入取决于远程桌面的焦点，中文输入、断线重连以及锁屏或断开 RDP 后的行为均需单独实测。

浏览器操作在执行中超时时，会话会拒绝后续请求并取消尚未执行的排队操作。已经发给浏览器的操作可能仍在运行，不能保证撤销；必须先检查远程界面状态，再启动新会话。

## Maa 流水线

模型可从本仓库复制，无需重新下载：

```powershell
New-Item -ItemType Directory -Force resource\model\ocr | Out-Null
Copy-Item ..\assets\MaaCommonAssets\OCR\ppocr_v5\zh_cn\* resource\model\ocr\ -Recurse
```

在 `resource/pipeline/` 放入经过现场验证的流水线，在 `resource/image/` 放入相应模板后运行：

```powershell
& $python run_pipeline.py <entry>
```

`Hotkey` 自定义动作接受 Playwright 键名列表，例如 `{"keys": ["Control", "o"]}`。PSIDE 的文字、按钮模板和坐标需从实际测试环境确认，不能直接把模拟页面的验证结果当作现场结论。

`config.json`、`state/`、`out/`、`debug/` 及复制的 OCR 模型已被 Git 忽略。登录态和截图可能包含敏感数据。

## 测试

```powershell
$env:PSAUTO_TEST_BROWSER_CHANNEL = 'chrome'
$env:PSAUTO_TEST_OCR = '1'
& $python -m unittest discover -s tests -v
```

测试使用本机临时 HTTP 页面和临时资源，不连接 JumpServer。未设置 `PSAUTO_TEST_BROWSER_CHANNEL` 时跳过浏览器集成测试；未设置 `PSAUTO_TEST_OCR` 时跳过 OCR 模型测试。
