2026-11-05，pshelp 回复主控 ps：AE 属性参数扩展独立冷审。

**最终修复状态（21:43:38 +08:00）：原 P2/P3 已修复，本 agent 只针对这两项独立 native 复验，2/2 通过。原始问题、反例和 SHA 保留在下文；最终修复 SHA 与验证边界见末尾附记。** Excel 实际执行仍未验收通过。

本轮标识 `ae-properties-eded96b-worktree-20261105`。首次冷审快照核对时间为 **2026-11-05 13:28:28 UTC / 21:28:28 +08:00**，当时 22 个文件 SHA 均匹配报告。仓库 `C:/Users/t-wangsen05/Desktop/MR3A-PS`，origin [qq765158273/MR3A-PS](https://github.com/qq765158273/MR3A-PS)，分支 `feat/psauto-jumpserver`，基线 HEAD 为 `eded96b1ec6e4e6f7f443f8eba5e9fdad8ec6ca9`。首次审查新增 17 个 AEProp 节点、9 张标签图、四个参数/服务文件、四个测试文件和四张属性 fixture，原始 22 个 SHA 保留为历史快照。

首次冷审结论（以下保留原始快照事实）：**当时快照存在 1 项 P2 对象身份保护缺口，以及 1 项 P3 空列表判断/负例覆盖缺口，不能无保留通过。** 其中 P2 在未修改的真实保存截图上，以实际 Maa 节点独立复现：请求名称只是实际 AE 名称的前缀时，属性入口仍点击、属性保存仍发送 Ctrl+S。None/False 参数分支、一次切换后验证、必需原生终态及证据错误隔离的目标检查通过。主控的成功创建样本成立，但不能替代这些身份反例。两项的后续修复不改写这次首次冷审已经发现问题的事实。

权限与方法：复用当前 agent，没有另起 agent；只读 Git diff、目标源码、标签/fixture 和本机已有证据。独立 native Maa 仅在仓库外临时目录运行，控制器只返回固定内存截图，点击/按键仅记录在 Python 列表，其他输入禁止；没有连接浏览器、DB、Process Scheduler，也没有创建或执行真实 PS 对象。参数/MCP schema/服务故障使用实际源码及内存替身检查。未修改源码、未提交；仓库内只写本报告。没有审核 psauto/demos、dept_probe_note_title.png 或用户未跟踪的 PSIDE 试验代码，也没有重审前轮性能。

1. **P2：新增属性入口、保存及保存反馈使用子串对象名，不能拒绝相似的其他 AE。** 位置：[ae.py:10](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/psauto/objects/ae.py:10) 绑定 `name_regex=identifier(request.name)`；新 [create_ae.json:4484](C:/Users/t-wangsen05/Desktop/MR3A-PS/assets/resource/pipeline/PSIDE/create_ae.json:4484)、第 4936 行、第 4982 行分别在 OpenFileMenu、Save、Saved 使用该值。`identifier()` 只转义名称并兼容下划线/空格，没有完整标识符边界或标题对象段约束。

   **独立 native 复现：** 使用主控真实目录 `out/objects/20261105_210620_078027` 中未改像素的 `040_A0_StructureSave_named.png` 和 `056_AEProp_Save.png`，实际 OCR 文本包含 `Application Designer - HRDEV - Untitled - GM_DEPT_XL3 (应用程序引擎程序)`。以真实 builder 绑定参数，保留各目标节点全部原生识别与动作，仅将其 next 清空以隔离观察单次节点。

   | 实际标题对象 | 请求对象 | OpenFileMenu | Save | Saved |
   | --- | --- | --- | --- | --- |
   | GM_DEPT_XL3 | GM_DEPT_XL3 | 通过，点击一次 File | 通过，发送一次 Ctrl+S | 通过 |
   | GM_DEPT_XL3 | **GM_DEPT_XL** | **仍通过并点击一次** | **仍通过并发送 Ctrl+S** | **仍通过** |
   | GM_DEPT_XL3 | GM_DEPT_XL4 | 拒绝，无点击 | 拒绝，无按键 | 拒绝 |

   两个名字均符合当前 AEName 校验，前缀案例没有依赖非法请求。第一次探查还确认请求 GM_DEPT 也会在该真实标题上通过入口。已有四项属性测试的“错误名”是 AET 行名称，不是属性入口的 AE 对象身份，故不能覆盖此问题。

   触发条件：到属性入口或属性保存时，活动标题属于名称包含请求名的另一个 AE，且其余菜单/关闭/保存模板满足。该条件一旦出现，新增保护不会在属性修改前拒绝。后续代码编辑器的既有完整对象/Step 保护可能停止代码粘贴，但不能撤销之前已经发生的属性保存。此次只在离线控制器中记录点击/按键，没有修改任何真实错误对象，也未证明现场已经发生错误对象写入。

   建议给属性流程使用具有完整标识符边界和标题对象段约束的独立身份绑定，至少覆盖入口、Save、Saved；保持 Program Properties 阶段仅用静态控件的既定设计，避免重新 OCR 灰色后台标题。补真实标题的前缀/后缀反例，并断言错误对象既不能点击 File，也不能发送 Ctrl+S。通用 identifier 的子串语义此前已存在；这里是新增属性保护沿用该语义造成的本轮缺口，不归因于先前 CLI/导出优化。

2. **P3：空状态列表只检查首行文字矩形，现有错误默认行负例在完整候选分支中仍进入 Qualify。** 位置：[create_ae.json:4592](C:/Users/t-wangsen05/Desktop/MR3A-PS/assets/resource/pipeline/PSIDE/create_ae.json:4592) 的候选列表 `StateBound → Qualify`，以及第 4638 行的 ColorMatch 区域 `[987,414,130,13]`。这只能证明首行这一小块全白，不能证明整个已有 AET 列表为空。

   **独立 native 复现：** 对真实 `ae_properties_state_bound.png` 使用与现有 `test_state_name_must_share_the_first_default_rows_checkbox` 完全相同的合成步骤：把首行名称复制到第二行，清空首行名称，其他标题/Qualify/checkbox 像素不变。单独 StateBound 确实拒绝；但按真实候选顺序运行 StateTab → `[StateBound, Qualify]`，保留 Qualify 原识别和点击，仅在该节点后停止观测，实际路径为 `AEProp_StateTab, AEProp_Qualify`，点击 `(840,376)` 一次。

   这证明错误默认行/下方仍有状态记录的画面会被首行全白检查当作可开始添加的画面；现有负例只跑 StateBound，漏掉 fallback 分支。该反例是从真实 fixture 合成的防护检查，未声称正常 PS 列表必定能产生这种空首行，也**未证明后续完整流程会接受错误默认记录、覆盖已有 AET 或保存成功**；后置 StateBound 仍可能停止，因此定为较低风险 P3。建议明确“整个列表为空”的判决，或在不满足正确首行默认记录时显式拒绝其他非空行，并把负例从 StateTab 的完整候选入口运行，断言不发生 Qualify/Paste/Add 动作。

已独立确认的正确范围：

- **属性配置早于代码粘贴。** 原生成功样本节点顺序为 A0_StructureSave_named（index 40）→ StateBound（51）→ RestartVerified（54）→ PropertiesSaved（57）→ A0_EditorReady（64）→ A0_Paste（66）。当前 builder 与该次 `pipeline_override.json` 完全一致。控制流没有把业务步骤搬入 Python，SQL/PeopleCode 仍以数据传递、剪贴板输入及保存反馈判决，不 OCR 正文。
- **None 与 False 分支。** 独立遍历 `{state_record=None/AET} × {disable_restart=None/False/True}` 六种组合的实际绑定图，均无可达的未绑定参数。None/None 保持旧路径；仅 state 跳过 restart；仅 False/True 跳过 state；False 仍进入属性配置，并要求 RestartVerified/PropertiesSaved，目标模板为 unchecked。字符串 yes/false、数字 0/1、列表、字典等六种非 bool 值均被 StrictBool 拒绝；四种非法状态表名被模型拒绝。
- **MCP 接口。** 对真实 create_server/schema 在内存中替换 ObjectService，None、False、True 均原样传入 AERequest；字符串 yes、数值 0、非法状态表名被 ToolError 拒绝。没有启动 stdio 子进程或调用真实自动化。公开 schema 中的状态表/布尔参数与模型约束相符。
- **默认首行与点击一次。** 四个现有 native 属性用例在独立初始化的临时 Toolkit/Tasker/资源和离线控制器下 **4/4 通过，0 跳过**。它们证明指定 AET 首行文字及 0.97 已选默认 checkbox 的组合、普通非空首行拒绝进入 Qualify，以及 restart 相反态最多点击一次、未生效即停。已为 True/False 的目标态不多点。上述 P3 指出的是其负例从完整候选入口运行时的另一条路径，未否定这些局部判决的实际结果。
- **原生标记约束。** 对真实 `_business_result` 独立做六种参数组合 × 四种缺失标记情形，共 24 组：缺少被请求的 StateBound、RestartVerified 或 Saved 会阻止 success；不被请求的标记不强求。Saved/Closed 原事实仍保留。以 GM_DEPT_XL3 实际 events/task_id 重放，得到三个属性标记和保存关闭均 true，没有依赖导出图像或 Node 的前驱 name。
- **证据错误隔离。** 用实际 ObjectService/AE builder 和 GM_DEPT_XL3 原始 events 作为内存任务完成结果，令 exporter 写部分 profile 后抛 OSError；state_record_bound/restart_verified/properties_saved/saved/closed 均 true，evidence_status=failed，next_operation_allowed=false；下一请求 evidence_unavailable。只提交一次，sink/client 各关闭一次。此次扩展没有发现证据或 finally 故障覆盖属性事实的回归。

独立 native 结果保存在仓库外 [independent_results.json](C:/Users/t-wangsen05/AppData/Local/Programs/Cygwin/tmp/pshelp-ae-props-final-jzrzaa1t/independent_results.json)，SHA-256 为 `11ba5afa5537faf674cf535b6f09a2ffb5ecfac577af77ea605299701a9489d2`；同目录包含 native 离线日志。执行过程曾有一次早期临时目录自动清理时 maafw.log 句柄仍打开，导致该脚本退出错误；最终复跑采用保留临时日志的目录，四项 native 测试及独立反例全部完成、进程退出码 0。没有把临时清理异常计为产品错误或测试通过。

主控证据核对，区别于独立实测：

- `out/dept_properties_native_tests.log` 为 4 项通过（2.960 秒），`out/dept_demo_unit_tests.log` 为 119 项、55 通过/64 显式跳过（3.993 秒）；本 agent 没有重跑普通全套，不把跳过项计通过，也不把主控四项与独立四项累加为八项。
- GM_DEPT_XL3 的 `dept_export_full_result3.json` 和原始 `out/objects/20261105_210620_078027` 支持主控完成创建、保存关闭及三个属性标记，工具 64.83 秒；summary 为 75 完成节点、2 次额外扫描、6 次候选未命中、0 节点失败/动作失败。原生事件跨度 53.390 秒、pipeline 53.38696 秒、导出 9.99963 秒；没有将这些重叠/不同口径重复相加。
- 主控说明 DBX 已确认默认 GM_DEPT_AET/Y、Disable Restart Y、编译长度 7264。指定本机证据中有 UI/native 属性标记和请求绑定，**本 agent 未执行 DB 查询，也未获得本轮单独 DBX 原始返回文件来作独立数据库确认**。上述 DBX 内容按主控提供的证据说明记录。
- 本轮工具 create_ae 本身不执行 AE。主控另一个 GM_DEPT_XLSX 的本地执行已到 PeopleCode，原生 AE 日志报告无法启动 JVM/RC8、未生成 Excel；此为主控运行结论，本 agent 在提供的本地索引中没有找到可独立核对的原生运行日志副本，未执行或修复运行环境。**GM_DEPT_XL3 的前端保存/编译/DB 定义通过不能表述成 Excel 导出成功。** 等待用户选择已有 Process Scheduler 环境是主控后续事项，不是本轮冷审需要操作的对象。psauto/demos 和临时 probe 图均未作为可提交验收代码判断。

建议顺序：先修 P2 的完整对象身份及错误对象不输入反例；随后补 P3 的整个列表空状态判决和完整 fallback 路径测试。保留现有 0.97 状态检查、一次点击后验证、参数 None/False 语义、原生属性标记及证据隔离。JVM/Process Scheduler 与实际导出另行验收，不用运行环境问题掩盖本轮身份缺口，也不以定义编译成功宣称业务导出成功。

未验证：错误对象在真实 PSIDE 中的实际属性修改、完整错误默认行场景是否可在普通交互中产生、当前候选分支后续是否可能改写已有 AET、不同 DPI/语言/主题、多状态记录滚动/遮挡、长期运行，以及 Excel 真实生成均未测试。独立反例的结论限于已说明的节点和实际/合成像素，不外推成已经发生数据损坏。

首次冷审目标文件 SHA-256（历史快照，最终修复差异见附记）：

```text
f042bf323f8b258177edf2317a02f99e97af5cd6b235f544e8a1b8fefe37e7f3  assets/resource/pipeline/PSIDE/create_ae.json
2b3244470f5996a102105524326844ffbff82efe7d6df630a557cba19fd194a8  psauto/psauto/objects/models.py
2222265ecaae723ed92efab1bc6e597a433d2c49561b6a23326632925ca31c49  psauto/psauto/objects/ae.py
0484c2ae02142c878f65fbbe9ee45daefbc476b5f5ae1798a66973d3e4174638  psauto/mcp_server.py
59d294eabafcf31f17379aa558bea30cfbfffdbd3fc976339e0d889cdaafd91d  psauto/psauto/objects/service.py
d0887fcb082315fdc3b4c49632614ed21885e38a36d532cf68a84604fb829357  psauto/tests/test_objects.py
89827e8825f699a8f317322e2b824a2705d54ba5ebf3d7be3f548a81ac500af2  psauto/tests/test_object_service.py
19f79c528df2b7fb6b1f0c4d0d23b8ca5794764c847619fa6c89837c24cb7e3d  psauto/tests/test_mcp_server.py
97ecedd562c93e0c662f92e46455fe8fa8517224af59e42d3083f24e7e8849dd  psauto/tests/test_ae_properties_recognition.py
9458e1cc04a499f1cfcbe351ea86b51169768b6c8e323e8d188d4837ca13482f  assets/resource/image/PSIDE/ae_add_state.png
d7ff5938b6007e5d802b770174db3aae99dbfef81b8f5122a317f93ac4b41f7b  assets/resource/image/PSIDE/ae_advanced_tab.png
e8d2d5be13b40217e3c4a3b59b01adf28eea78d7349d25a81291367b662b30b3  assets/resource/image/PSIDE/ae_definition_properties.png
33c6c2ea3a93953e1bace3e4ee6411d8ec7889452f01b85ac633ff1c1cf9559b  assets/resource/image/PSIDE/ae_file_menu.png
42c89050b49d212072ab131abd9868bc5525dd731e150de92e2fe72ed409c4c3  assets/resource/image/PSIDE/ae_get_list.png
fd118bccfbba79c189aee25522d3b4d8dad505085cd10edb13c654273823b0bc  assets/resource/image/PSIDE/ae_properties_ok.png
8a0fa844e124b1368149627d9f8606e74aa0129a8f2956900df375c2a87e53ff  assets/resource/image/PSIDE/ae_properties_title.png
1c5c1aafa8aa5d9212d1744b9b5ae85d8f69b61973308c5e5b876a7047ce6f6c  assets/resource/image/PSIDE/ae_qualify_label.png
a4fe40054f0d0ddf7b4ca96bcc4298172c17c2f03d9f74aaa7deee12c509e4b4  assets/resource/image/PSIDE/ae_state_tab.png
8067614a6b06577f6a52de1a43ebb5f30e755e408b836dab081da6f2d660148f  psauto/tests/fixtures/vision/ae_properties_restart_off.png
1dce32f8b396f555bd0cd8d0efa596ae2abef10e395d17a1c2aa048f1267324c  psauto/tests/fixtures/vision/ae_properties_restart_on.png
ccfc8c28d463a6fd16d78643d4c1d434dd5facd3ade51ee49302dcd32d9aa83d  psauto/tests/fixtures/vision/ae_properties_state_bound.png
617ec52cea57ae3ec6a2a0fd0eac842edf1d414db400bca4269f5b979530f3c8  psauto/tests/fixtures/vision/ae_properties_state_empty.png
```

报告写入后仅用 tmux display-message 通知 `ps:0.0`。目标 pane 当前是 shell，不发送自然语言加 Enter；主控按约定主动读取报告，通知不等于已收到全文。

**P2/P3 最终修复补核附记：2026-11-05 13:43:38 UTC / 21:43:38 +08:00。** 本次按主控要求只复核两个问题的修复与 SHA，没有重审其他模块或重跑完整测试，没有浏览器、DB、真实对象或 AE 执行操作。

- **P2 已关闭。** [ae.py:11](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/psauto/objects/ae.py:11) 新增独立 `property_identity_regex`：`(?:^|-\s*)` 后匹配对象名，对象名后要求空白和中/英文左括号，定位标题中的完整对象段。OpenFileMenu、Save、Saved 三节点均改用它，未放宽通用 name_regex 或状态表名规则。它拒绝 GM_DEPT_XL / GM_DEPT 等真实标题前缀，并保留 GM_DEPT_XL3 正例。
- **P3 已关闭。** Qualify 的空列表判断改为 Selected 列表内部 `[966,414,159,184]`，要求全部 29,256 像素为白色；不再只判首行 130×13 小块。新增用例从 StateTab 的真实候选列表 `[StateBound,Qualify]` 进入，覆盖空列表（允许一次 Qualify）、正确默认记录（无需 Qualify）、首行名称空白而下方仍有记录（拒绝，无点击）。错误态无法进入 Qualify，后续 Clear/Paste/Add 分支也不会执行。
- **本 agent 独立 native 实测：2/2 用例通过，0 失败、0 错误、0 跳过，7.976 秒，进程退出码 0。** 只运行 [test_ae_properties_recognition.py:75](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/tests/test_ae_properties_recognition.py:75) 的标题前缀反例，以及同文件第 57 行的完整状态候选反例；资源/模型来自当前仓库，Toolkit/native 日志和控制器完全在仓库外临时目录。点击/按键仍仅记录在内存，其他输入被禁止。前一用例对 OpenFileMenu/Save/Saved 三节点各覆盖正确名、两个前缀名、不同尾号，共 12 个子情形：错误名不点击菜单、不发送 Ctrl+S、不生成 Saved 成功。后一用例覆盖上述 3 个列表布局。没有将主控六项日志当作本 agent 独立运行结果。
- 新增真实标题 fixture 与首次复现的原图逐字节一致：`ae_properties_before_open.png` 等于原 `040_A0_StructureSave_named.png`，`ae_properties_before_save.png` 等于原 `056_AEProp_Save.png`。因此修复验证没有通过更换标题像素回避原反例。
- 独立日志为 [independent_native_fix_tests.log](C:/Users/t-wangsen05/AppData/Local/Programs/Cygwin/tmp/pshelp-ae-props-fix-228w7q_5/independent_native_fix_tests.log)，SHA `c036a1b744ab8fa42831b2927b8b699c2f3da9e97c94d34139df6905e74dd1ef`；同目录 [independent_results.json](C:/Users/t-wangsen05/AppData/Local/Programs/Cygwin/tmp/pshelp-ae-props-fix-228w7q_5/independent_results.json) SHA `f86cb6938309a0934b2e45581ac10ea0d23076fd219f74f6cfa355c3c2e23bc1`。

最终修复代码/fixture SHA（其余首次快照 19 个文件经核对未变，原始 SHA 保留上表）：

```text
b645f881db0672fe1788f8e67a87506bfb614e48d2a3e11ea9d1c3ed904bbbe5  assets/resource/pipeline/PSIDE/create_ae.json
fb05da4655f80d4e6985a4f86cfd18b66ced459d3a33b99e47ddc8c469d137aa  psauto/psauto/objects/ae.py
7fdf782449b807b29dbb0e32d0a0998dcd2fc78c773051a3a5fbf50de19cd3e2  psauto/tests/test_ae_properties_recognition.py
a14ec6a4081af9a651ec75d9b31c70c90a9f4cfbc2d991ff15267c4fe80858c5  psauto/tests/fixtures/vision/ae_properties_before_open.png
98014152ce4760296c168e0ed651d8d748284187d6da84817abb048844755d27  psauto/tests/fixtures/vision/ae_properties_before_save.png
```

主控最终证据，仅作已有文件核对：

- 原 `dept_properties_native_tests.log`（4 项）与 `dept_demo_unit_tests.log`（119 项）是首次冷审日志。修复后的文件是 `out/dept_properties_native_tests_final.log`：**6 项通过，7.162 秒**，SHA `222c50a5d710619a32748965365160c03033f5dc9261dceba114618c7e7161ab`；以及 `out/dept_demo_unit_tests_final.log`：**121 项、55 通过/66 跳过，4.335 秒**，SHA `187804de8a9f5122bfe8ca44251be6b8b6f448b9d5a665fcc47185fc44e9b050`。不能把新旧日志或独立两项累计成整体通过率。
- 主控从头新 stdio MCP 创建 GM_DEPT_XL4 的 `out/dept_export_full_result4.json`（SHA `31f8d842c1e2400b9a3e64134cc2b1fd4f8ae6be008e6820ccf6073322b01682`）明确为 66.50 秒、saved_and_closed、saved/workspace_ready、三个属性标记、evidence complete、next_operation_allowed 均为 true。对应 `out/objects/20261105_213633_731943` summary 为 75/75 节点，3 次额外扫描、7 次候选未命中，0 节点/动作失败；原始 report 包含 StateBound、RestartVerified、PropertiesSaved 和 SavedAndClosed。此为主控真实运行的记录，本 agent 没有独立启动 MCP 或操作 UI。
- 主控新增 [dbx.json](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/docs/images/acceptance-ae-properties-20261105/dbx.json)（SHA `6a1913917ae5b9969b3bcd8e27995b68cc96298e9537af4ead6bd85691232f7a`）补齐了首次报告尚未拿到的数据库返回：其中列出 GM_DEPT_XL3 默认 GM_DEPT_AET/Y、Disable Restart Y、PROGLEN 7264。这个文件核对属于读取主控查询结果，不是本 agent 独立 DB 验收，也不据此给 GM_DEPT_XL4 添加未执行的 DB 检查。
- 已独立查看主控的 [ae_runtime_jvm_error.png](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/docs/images/acceptance-ae-properties-20261105/ae_runtime_jvm_error.png)（SHA `f64cd173ae4f9c53ed0146b111f9700b6ff9fce7a62912ddfbda6ee69c2ceb5f`）：原生 PeopleTools 8.57.11 日志显示 GM_DEPT_XLSX 已到 MAIN.Step01 PeopleCode，报“无法启动 Java 虚拟机 (2,766)”并以 RC=8 异常终止。此次是独立阅图，仍不是本 agent 执行 AE。它补齐了首次报告缺少的日志副本，不代表成功生成 Excel。

最终结论：**首次冷审的 P2/P3 均已在限定修复范围内关闭；两条独立 native 确认用例通过，未发现该修复留下的确定问题。** 保留首次问题和反例历史，不改称原始快照已经通过。新 MCP authoring 的成功由主控证据记录；Excel 业务执行仍因本地 JVM 无法启动而未验收成功，不将定义创建、属性保存、编译长度或 DB 元数据通过表述为导出成功。
