2026-11-05，pshelp 回复主控 ps：save_project 独立只读审核。

**最终定向补核状态（22:50:17 +08:00）：主控的查重拒绝和三类型创建证据已核对。补核发现的 Record 滚动关联列表 P2（末端模板无法证明隐藏首部）随后已增加末端→滚动→首部保护；独立 native 定向用例及原输入失效模型复验通过，该缺口在指定固定列表视图范围内关闭。原问题、修复前模型及新 SHA/边界均保留在文末。**

轮次 `project-capability-89a71bb-20261105`。仓库 `C:/Users/t-wangsen05/Desktop/MR3A-PS`，origin [qq765158273/MR3A-PS](https://github.com/qq765158273/MR3A-PS)，分支 `feat/psauto-jumpserver`，基线/当前 HEAD 为 `89a71bbc562031384dcd2e1faa9d1d07842c133e`。首次源码快照核对时间为 **2026-11-05 14:40:07 UTC / 22:40:07 +08:00**，当时 30 个原始文件 SHA 均匹配。首次范围是主控列出的 Project 模型/builder/Pipeline、service 标记、MCP/调用入口、四个测试、14 张标签图及六张 fixture；后续同范围三个文件及新增首部模板/fixture 的定向补核见末尾，原始 SHA 保留历史。

首次复核结论（可见区域及当时执行的检查范围）：**未发现确定的唯一结果绕过、前缀身份误通过、错误类型插入、未生效点击重复提交或缺失原生标记误报成功。** 查重冲突路径没有通向插入或保存；保存后的释放使用精确工程标题、Project 选择模板和空 Untitled 终态。首次复核尚未覆盖滚动列表隐藏首部的选中状态，后续补核结论见文末。没有独立真实 UI/DB 验收，也不能将这些有限截图证明扩大到任意树视图或界面布局下的空性保证。

权限与方法：复用当前 agent，未另起 agent；没有重新审核 AE 属性、导出性能或未验收 demos。仅读取指定源码、Git diff 和主控本机证据；自己在仓库外临时目录创建离线 Toolkit/native 控制器，画面为内存 fixture，点击/按键仅记录到列表，其他输入被禁止。参数、MCP schema 和服务故障在内存替身中验证，没有启动业务浏览器、数据库、真实 MCP 或 AE，没有创建/修改业务对象、源码或提交。仓库内仅写本报告。

**独立实际运行结果：**

- 独立执行 `test_projects` 的 **2 项参数测试 + 3 项 native 测试，5/5 通过，0 失败/错误，14.093 秒，进程最终退出码 0**。初始化和日志位于仓库外，没有调用测试原有的仓库日志初始化。native 用例覆盖三类定义的严格名称、Related Definitions 全选像素、结果蓝色选中、blank/2/11 数字反例、已保存工程完整名与前缀拒绝、空工程与非空/模态拒绝。
- 在 AE 真实选中 fixture 的同一位置另行绘制数字，调用实际 `P0_Insert` 原生节点，独立测试 **0/1/2/10/11/12/21/100/101/111/1000/1100 共 12 种计数**，仅 1 通过并点击一次，其他计数均无点击。这是该字体/固定 ROI 的像素反例矩阵，未宣称覆盖任意字体、DPI 或 OCR 误识别。
- AE fixture 请求为 Record 或 Field 时，实际类型模板不匹配，均拒绝且无点击；没有依赖名称相同来绕过类型检查。
- 独立连接 `P0_Insert → P0_Inserted` 反馈链：点击返回成功但图像不变时，任务失败且只点击 1 次，不重放；点击后替换为真实 `project_ae_inserted.png` 时，任务通过，路径确实包含 P0_Inserted，仍只点击 1 次。没有把输入回执等同于插入反馈。
- 参数图独立覆盖 1、2、3、20 项清单：最后请求槽位正确跳到 P_CloseDialog，后续未请求槽位不可达，所有可达参数均已绑定、on_error 为空。20 组展开节点经规范化比较结构一致，没有发现复制后的槽位差异。
- ProjectDefinition 的 AE/Record/Field 分别接受 12/15/18 字符并拒绝再多一字符。清单长度 1–20、按 type+name 去重、GM 工程名前缀及最长 15 字符在实际模型中校验。**15 是本实现视觉核验的限制，不是 PeopleSoft 30 字符平台上限。** 字符宽度、其他字体下全部 15 字符是否都可完整显示，仍需更多截图，不把模型上限等同于全部 UI 字符组合的已验收范围。
- 对真实 create_server 在内存中替换 ObjectService，save_project schema 的枚举为 AE/Record/Field；有效清单原样进入 ProjectRequest，非法工程名、空清单及通配符名称均被拒绝。未调用原自动化。call_mcp.py 相对基线仅把 save_project 加入既有受限 tool choices，没有添加执行 AE、导出文件或 DB 写入入口。

独立 native 日志和附加像素反例保存在仓库外：

- [independent_native.log](C:/Users/t-wangsen05/AppData/Local/Programs/Cygwin/tmp/pshelp-project-kou4h245/independent_native.log)，SHA `1a31e2474b746f0e6ddae05cad55fabd29d2eb3d8d2162cf812c329b72093d9f`。
- [independent_results.json](C:/Users/t-wangsen05/AppData/Local/Programs/Cygwin/tmp/pshelp-project-kou4h245/independent_results.json)，SHA `91e1493ab7dedcc0f7f9950518e18f24c79eb2482c50d5b30ae5df85d0e1b7fa`。

**控制流与保护的判断：**

1. 空工程入口要求 HRDEV/Untitled 标题、0.97 idle toolbar、左侧成员区域全白及中央操作区全灰。已有 fixture 中，非空成员、插入对话框、已命名 Project 均不能作为空入口。查重取消后 P_InsertOpen 还检查空成员区，未发现直接对已有保存工程插入的路径。当前证据只能确认这些固定区域/视图的保护；对折叠、筛选、Upgrade 等其他树视图或特殊 UI 状态，不能仅凭静态结构断言不会存在隐藏成员，见未验证项。
2. 每个槽位先 New Search，选类型并验证静态类型模板，输入并 blur 后以完整名称规则检查，再要求结果区域为空才 Search。RelatedFocus/Select/Insert 均要求返回名称与 `^\s*1\s*$` 数字。Insert 还要求正确类型、对应 Related 全选模板 0.97，以及结果行蓝色区域。所用名称是带首尾锚点的完整行；独立 native 前缀反例已拒绝。
3. Pn_Inserted 要求插入对话框、对应类型和原生 inserted feedback；输入动作之后必须另一次识别反馈，不存在失败后回跳到 Insert 的循环。它表示本槽位获得原生插入反馈，**definitions_added 是请求槽位反馈数，不是最终 Project 原生成员总数**，不能将 2 写成工程只有 2 个成员。
4. 查重找到已有 Project 后，路径为 already_exists → ConflictNew → ConflictSelect → ConflictOK → conflict_closed。独立遍历确认该分支没有 InputText、插入槽位、SaveMenu 或 Save_ok；它只以完整工程标题和中央空操作区为前提，新建 Project 并确认空 Untitled。没有发现该分支写入已有工程成员的动作。该路径的安全判断是静态加终态 fixture 证据，未独立在真实已有 Project 上操作。
5. 正常保存先关闭 Insert 对话框，再以 Untitled 标题/idle toolbar/中央空区打开 Save Project；命名框进行完整名称识别，保存后又检查 `HRDEV - <完整工程名>`。P_CloseNew 在精确标题通过后才发送 Ctrl+N；Project 选项模板 0.97 通过才点 OK，最后必须看见完整空 Untitled。未知覆盖/保存提示没有回复节点或 on_error 分支；出现时应停在识别超时，未见直接确认未知提示的路径。真实并发竞争提示尚未注入。

**原生标记及证据错误隔离的独立检查：**

- 直接执行当前 `_business_result`：两项请求必须同时有 P0_Inserted、P1_Inserted、Saved、SavedAndClosed，才可 success。分别缺少两个插入标记或缺关闭标记时均不成功；来自其他 task_id 或 completed=false 的同名标记不会补足本任务。共 4 组故障/正常组合符合预期。
- 用主控真实 55 节点 events 和 report task_id 重放当前函数，得到 saved_and_closed、saved/workspace_ready=true、definitions_added=2，与归档 MCP 返回一致；这是读取旧事件的函数核对，不是本 agent 再执行 UI。
- 将真实 ProjectRequest、builder、ObjectService 和上述 events 接入内存替身，令导出在写少量 profile 后抛 OSError。返回仍保留 saved/closed 和 definitions_added=2，evidence_status=failed、next_operation_allowed=false；第二次调用 evidence_unavailable，业务仅提交 1 次，sink/client 各关闭 1 次。没有证据错误覆盖业务事实或重复执行。缺少插入标记时也不会因为 Saved/Closed 已出现而误报成功。

**主控证据读取，区别于独立实测：**

`out/project_full_result.json` 对 GM_DEPT_EXPORT 返回 success、saved_and_closed、definitions_added=2、evidence complete、允许下一操作。`out/objects/20261105_222241_025083` 的 request 是 AE GM_DEPT_XL4 和 Record GM_DEPT_AET；report/summary/events 支持 55/55 完成节点、450 事件、2 次额外扫描、3 次候选未命中、0 节点/动作失败。P0/P1_Inserted、Saved、SavedAndClosed 均 completed 且规则通过。原生跨度 37.250 秒，pipeline 37.25365 秒，导出 9.86156 秒；这些是不同阶段/测量口径，不重复相加。

主控已归档的 [dbx.json](C:/Users/t-wangsen05/Desktop/MR3A-PS/psauto/docs/images/acceptance-project-20261105/dbx.json)（SHA `fe6b5c07c10b5b78833cc5a3c3ade0d7bc2cda0bf66c022c98d361daa4be0a29`）列出 GM_DEPT_EXPORT 的 10 条成员，包括 AE 33、Section 34、PeopleCode 43、AET 及字段/字段标签，既有编译长度 7264。它支持主控“显式两项定义包含 Related Definitions”的结果，不是本 agent 独立 DB 查询，也不表示 Excel 已执行成功。

主控日志 `project_native_tests_final.log` 为 5 项通过（8.903 秒，SHA `fc4c39a0f2af46f25e73fcf622ed1e7a373bebac5a75e0827f6d316ab9664890`），`project_unit_tests.log` 为 127 项、58 通过/69 显式跳过（4.694 秒，SHA `116067b24d669c0407eaf16426cd349d3b100b40ded601425029600f5ac3ea4c`）。它们与本 agent 独立五项重跑有重叠，不累加为十项或整体成功率；普通全套未由本 agent 重跑。当前 Project 测试源码已包含 2/11 数字负例，本 agent 另用更宽数字矩阵验证了实际结果。

**首次结果与建议顺序（隐藏类别补核发现见文末）：** 首次检查范围内未发现确定缺陷。后续若扩充可信运行范围，优先增加已存在 Project 的真实查重拒绝/释放、真实保存名称竞争的停止证据；再覆盖 Field 完整 UI 入口与 20 项清单端到端。其中查重和三类型的主控后续证据现已补入附记。对空工程判决应继续维护不同树视图和可见成员反例；本轮没有证明某种未覆盖布局必然导致丢数据，也没有把“没有观察到问题”当成任意状态安全保证。

未由本 agent 实测的项目：真实用户工程的丢弃/覆盖风险场景、不同树展开/滚动/筛选状态、不同 DPI/语言/字体、20 项 UI 连续插入、Field 类型完整真实 UI 流程、已有 Project 查重真实分支及并发保存冲突、长期运行。主控后续已提供查重/三类型真实流程，见末尾证据来源区分。本 agent 未运行 AE、未导出文件或查询数据库。Excel 仍因本地 JVM 启动失败未验收；保存 Project 和读取编译长度不能替代 Excel 运行/文件验收。

**SHA 口径：** 以下均为 **工作区原始文件字节 SHA-256**，与主控提供的 30 个值一致，不是 Git blob ID。create_project.json 当前含 11,188 个 CRLF，test_projects.py 含 122 个 CRLF。若只将 CRLF 规范为 LF，对应 SHA 分别变为 `23ef1d29e6d10d43b6ad0268c0992566e268304560966ad5bf04cb921ea97b7d`、`bb89c489205742f3208aae079174b15e17c18ddfcb752612ce8ac61ee420ca70`。Git 提交/显示可能采用规范化文本，不能把这个换行差异误判为代码变化。

```text
8cdb8028f8f02f35db2ab1b26728e4dd027d359b87ee6998643623a5d3a5d3f7  assets/resource/pipeline/PSIDE/create_project.json
a2630919ea43238f71aebb5747192cefa73363b5329519a3853f92aaf4dff38e  psauto/psauto/objects/project.py
c2cc846ade6bd8712d0b2b790ee65ac992504b7301a1297c52eb1ee86c1385a8  psauto/psauto/objects/models.py
8716090d574c877f0f485a8f925b9a5e80dba2057e78a07619d6c2de5c9284ed  psauto/psauto/objects/service.py
6b87e02a2b4ac0c554ecb0668a7c0d0b96664b09628a079d2476393a76ae5c7f  psauto/mcp_server.py
40f399921127e9a6e2b4cdd2fe5579aad2fac7462fd7b450dae5fa7fe59b03f4  psauto/call_mcp.py
0a7d4d5da7d5ba60e4a0dddde4052bf00b301a4941469de729f29fc359a84813  psauto/tests/test_projects.py
a48e4af37f09e139f2af4353d897582dca863a45859493795a468d2825493cf2  psauto/tests/test_objects.py
e122aca0139fd3b6a038823a2014f071c2b5ce3fd4c290de1a474ca976be70c1  psauto/tests/test_object_service.py
249aa15cfceac240635f27957b1e13cbc9030c4ce6cbd0c0c3dd460a51929aae  psauto/tests/test_mcp_server.py
ca2c483a4a97fdff4631c5f9cc96e3e81ab3372f184bb04babf0681376ed9973  assets/resource/image/PSIDE/project_close_button.png
d174fc5836f2210da24533536cc93e15ee4a07f2070f702aa0c4a8fde16e8c6b  assets/resource/image/PSIDE/project_inserted_feedback.png
6dca14c26fadddb07b7f5684d2bad5c9ab74b28aef29e438bffd149ec01d7618  assets/resource/image/PSIDE/project_insert_title.png
71b5e3fbfe23af00b74fb47090f1f48f6ef19c8c2f5658282e1bc7a51f67f57e  assets/resource/image/PSIDE/project_lookup_type.png
4726cc5261e75720080cd5e476625a1722a9b19e17a3edde60768a8a0dde2451  assets/resource/image/PSIDE/project_related_ae_selected.png
ed7910f2ac63c3fff58644870f779daf5f8e1966bb5de8137965e949c4f32c9f  assets/resource/image/PSIDE/project_related_field_selected.png
a1f23b4ed6b7ba255ff414b0bd24a7aaa1589689660670378cd3f58c6a6e758b  assets/resource/image/PSIDE/project_related_record_selected.png
9284cd03f75feec23b8128339df8fa24cbacb529fb05786bf5065de89b18d2c7  assets/resource/image/PSIDE/project_save_menu.png
33c873bd5ef164bcac200a6c7167a7f179708eff79c7ef4f04d4ce73a76ee352  assets/resource/image/PSIDE/project_save_title.png
027f26bad85d9c6c7ce21f39c7da86dd438e064080dd17586d9f23ada2015ac4  assets/resource/image/PSIDE/project_search_button.png
81de37b3ab668c495077cc4349f537bb20d0f961c24b5db65ea83d744e733848  assets/resource/image/PSIDE/project_type_ae.png
bec1fdbebccb68c0bbef9c76780f246c97fc24113926bc11b037facf421e51ec  assets/resource/image/PSIDE/project_type_field.png
236e42b502170de01eb6f1c15ea0650672deae2439ab38ecbceeb98d48f7cad6  assets/resource/image/PSIDE/project_type_record.png
2b4faa6878562484351c4d2e26b8421c0cb0be5fdd183e9e5dd634eca49f6262  assets/resource/image/PSIDE/new_definition_project_selected.png
655d84b29658151ab11e4507ab15521e63f4eb9e8ce4c4e22e2b703b6fbc3152  psauto/tests/fixtures/vision/project_ae_inserted.png
79544b492f0844c7f02a2e02ff03658bf26dc5ba0641132ed5b8c425a1f41839  psauto/tests/fixtures/vision/project_ae_selected.png
832c9ed313c34b2c7585c38737d6d3c92052bba9535a4e90cefc179bc8b27964  psauto/tests/fixtures/vision/project_empty.png
44a209cccec7e39d377fd299d3d1735d207f370789519193b5d4d7741ba77ce9  psauto/tests/fixtures/vision/project_field_selected.png
e8e88654cdbe8965a05015e6a939600f7596561b48d359445da45eb61fa9e864  psauto/tests/fixtures/vision/project_record_selected.png
3cd73c57fda320b425128b7edbcee4e4a4ae504a8afb63681d68569211f4ea7d  psauto/tests/fixtures/vision/project_saved.png
```

正式报告先保存，随后只向 `ps:0.0` 发送一次 tmux display-message 通知。目标 pane 为 shell，不向 shell 提交自然语言命令；主控按约定主动读取报告。

**Project 连续验收与隐藏关联类别补核：2026-11-05 14:44:07 UTC / 22:44:07 +08:00。** 本次只读主控新增证据、现有 Record fixture/节点，并在仓库外做相关 native 输入故障模型；没有浏览器、DB 或真实 Project 操作，源码 30 个原始 SHA 仍全部与初始快照一致。

主控新增真实结果与 DBX 文件核对：

- `continuation_results.json` 记录同一次连续运行先拒绝 GM_DEPT_EXPORT：`success:false/status:already_exists/definitions_added:0`，同时 workspace_ready、evidence complete、next_operation_allowed 为 true；随后 GM_PS_PROJ_T 三种定义完整保存关闭，definitions_added=3、证据 complete、允许下一操作。主控说明是同一 MCP 实例；这些是主控运行记录，不是本 agent 独立执行。
- 将新 `continuation_dbx.json` 的结构化 rows 与原 `dbx.json` 比较，GM_DEPT_EXPORT 的 LASTUPDDTTM 和 10 条成员逐项完全相同；GM_PS_PROJ_T 返回 12 条成员。它支持主控“查重没有修改原工程、三类型样本已完成”的结论。本 agent 只比较保存的结果，没有查询数据库。
- 两个新增证据的原始 SHA 分别为 `934ec7404c88577440fd24590a003e43b0c43c159353fe55f2f2822539408497`（continuation_results.json）、`4c5de119c4991da05dfc5d5ca85573f82729bdb35381da213c483eb6e878f598`（continuation_dbx.json），均位于 `psauto/docs/images/acceptance-project-20261105/`。最终 native 日志仍为 5 项通过，测试源码含 2/11 计数反例；不与先前独立五项叠加统计。

**补核发现的 P2（修复前快照，后续已关闭）：Record 的滚动末端选中模板不足以证明隐藏首部类别已选中。** 位置：[create_project.json:819](C:/Users/t-wangsen05/Desktop/MR3A-PS/assets/resource/pipeline/PSIDE/create_project.json:819) 的 `Pn_RelatedAll`（各槽位同构，Home → Shift+End），以及第 949 行起 Insert 的 Related 模板检查。Record 模板 `project_related_record_selected.png` 仅 133×77 像素，fixture 已滚动至列表末端，画面显示 Fields、Indexes、Record Fields、Record PeopleCode、SubRecord、Translate Values 等末端类别；首部类别处于视口之外。

静态判断：当 Related 列表确实保持焦点且远端按标准扩展选择语义处理 Home 和 Shift+End 时，命令意图是从首项选至末项，正常路径合理。但键盘动作成功回执不等于 RDP 端的选择已生效，末端截图也观察不到隐藏首部。当前没有顶部选中、跨页选择数或其他等价判决。因此“已发送全选序列”与“已验证全部类别选中”必须分开。

独立 native 故障模型：继续使用未改像素的 `project_record_selected.png`，实际运行当前 `P0_RelatedAll → P0_Select → P0_Insert`，仅令 Insert 后停止，避免后续无关步骤。离线控制器记录收到的 `[36,65571]`（Home、Shift+End）并都返回成功；设置两种输入语义模型：一是 Home 正常令锚点到隐藏首部，二是列表原先在末端、首部未选，Home 未生效，Shift+End 只扩选当前可见首项至末项。两种最终可见末端图像相同，原生节点均通过，均走到 Insert，并产生结果行点击和 Insert 点击各 1 次。

其中 `hidden_first_selected_in_model` 是注入的状态假设，不是从 PSIDE 或 native SDK 读取的真实隐藏状态；此实验确认的是**当前 guard 无法区分隐藏首部未选这一输入失效模型**，不是证明当前现场真的丢过 Home、已经生成了不完整工程，或原 Project 样本有成员遗漏。触发条件需要 Related 列表已滚动、隐藏首部未选，且首部定位/选择步骤在远端未生效但输入回执成功；这样的条件不在现有末端模板保护中。

独立模型结果为 [independent_results.json](C:/Users/t-wangsen05/AppData/Local/Programs/Cygwin/tmp/pshelp-project-hidden-related-pzz_5ijv/independent_results.json)，SHA `50e52e26963b0eea29539df0359184f6d2dd86cf8f6f2cb2db382fa98dfa3d7c`。两种模型均使用同一真实可见 fixture、实际 native 节点及真实 key 列表；未向浏览器、RDP 或 DB 发输入。

现有 10/12 条 DBX 成员不能单独消除此缺口：它们证明这两个具体源定义/工程样本的结果，未证明隐藏类别在 UI 中确实全选；某隐藏类别即使没有被选中，源定义也可能本来没有该类关联成员，故该样本的最终成员仍相同。不能从缺少某类成员倒推它被漏选，也不能反向把当前成员数当成所有 Record 关联类型的覆盖证明。

建议补一个不改变选择状态的视口检查：在已验证的滚动/焦点操作下确认首部选中，再确认末端选中，或使用 UI 可见且已验证的等价选择计数。滚动方式是否保持选择需先离线/受控验证，不能直接再发 Home 就宣称确认，因为它可能清除扩展选择。随后补“Home 无效/锚点未到首部但末端全蓝”时不能 Insert 的反例；最好使用确有隐藏首部关联定义的 Record 做后续真实样本。不要依赖插入后的通用 inserted 文本来证明全部关联类别，因为少选类别时它仍可能报告部分成员已插入。

修复前补核结论：查重拒绝和三类型真实创建已有主控证据支持，原工程未被改写；唯一计数/名称/类型/反馈的前述通过结论不变。但当时 **Record 全部 Related Definitions 的 UI 完整性保证有 P2 验证缺口**。该发现不等于已经发生成员丢失，亦不涉及 Excel 运行验收；后续闭环如下。

**Record 首部选择保护的定向修复复验：2026-11-05 14:50:17 UTC / 22:50:17 +08:00。** 报告收尾核对时发现同范围源码已有补充，故只对该新增保护检查，没有重跑全部能力/性能审核或操作业务浏览器、数据库。

- 新 builder 为 Record 把 Select 后续改为 `RelatedScrollTop → RelatedScrollAgain → Insert`。第一滚动节点先检查旧末端 Related 模板、正确类型/名称/唯一计数/结果蓝色，再点击滚动条上箭头；第二滚动节点继续检查类型、名称、计数和结果蓝色，再点上箭头。Insert 的 Record 模板改为新增 `project_related_record_top_selected.png`，验证原先隐藏的首部类别已选中。滚动使用箭头点击而非再发会改变选择的 Home；AE、Field 仍走原直接 Insert 路径。独立绑定图检查确认只有 Record 可达这两个滚动节点，三种类型均无可达的未绑定参数。
- 本 agent 在独立临时 Toolkit/内存控制器中运行新增 `test_record_scroll_checks_hidden_top_categories_before_insert`：**1 项通过，3.948 秒，0 失败/错误，进程退出码 0**。保留真实末端 fixture，模拟两次滚动后切换为真实首部 fixture。首部已选时发生两次箭头和一次 Insert 点击；缺首部选中时只发生两次箭头点击，没有 Insert。
- 另从实际 `RelatedAll → Select → RelatedScrollTop → RelatedScrollAgain → Insert` 重跑原 Home 失效模型：正常 Home 语义模型通过，共 4 次点击（结果行、两次箭头、Insert）；末端可见状态相同但首部未选的模型失败，共 3 次点击（没有 Insert）。两种模型都接收同样 `[36,65571]` 并返回输入回执成功，因此新拒绝来自首部像素 guard，而不是输入 API 假造失败。这里仍是输入故障模型，不是本 agent 操作真实列表。
- 独立日志 [native_fix_test.log](C:/Users/t-wangsen05/AppData/Local/Programs/Cygwin/tmp/pshelp-project-related-fix-g5plause/native_fix_test.log) SHA 为 `86fca9b7d7cc2a9bc29c8a39143de71a4a4898756751e47451e43d017ad29197`；[independent_results.json](C:/Users/t-wangsen05/AppData/Local/Programs/Cygwin/tmp/pshelp-project-related-fix-g5plause/independent_results.json) SHA 为 `61715d89554e9d4eb22c0e3fce100e6d869ce2f0b8e1fc4140c275e24a03f1a5`。
- 截至该补核时间，所读主控 `project_native_tests_final.log` 仍是原五项日志，`project_unit_tests.log` 仍为 127 项记录；不将其说成已经运行新增加的首部测试。上面的新增定向 native 结果是本 agent 实际运行，不与旧五项日志合计。

最终修复文件原始字节 SHA（初次 30 个目标中仅下列前三个变更，另增两张图；其余 27 个目标 SHA 已核对未变。原表保留为修复前历史，最终目标共 32 个）：

```text
13f28ebdae33d0bd7c31272df668ca4231c1147f456ffe3c0c0d7b0af0899f4b  assets/resource/pipeline/PSIDE/create_project.json
b2ddad4467aa07a2ff99ec63c0793bcc77aa92cee65374a6e2064c1da3cf2233  psauto/psauto/objects/project.py
3cefd4072b2e4c841980693f1cfb47967334a34ef7c42afaee50a1372f1d5789  psauto/tests/test_projects.py
03a08fdbc49b588d1fc7a1fe7acbc67e0d357d363e1d7ed7156315c2e139ede3  assets/resource/image/PSIDE/project_related_record_top_selected.png
ebaf5560ea63e843e18220b2434118a931945c703ebd3b13cf31005d56e8439d  psauto/tests/fixtures/vision/project_record_top_selected.png
```

最终判断：**旧末端模板本身依然不足以证明隐藏首部；新增首部/末端双端保护已在指定固定列表布局与独立输入失效模型范围内关闭这项 P2，未发现其遗留的确定问题。** 这不等于证明任意新增类别、不同 UI 版本或布局都已覆盖。主控此前连续真实样本早于这次 guard 补充，不能当作新增 guard 的真实 UI 验收；滚动箭头在真实 UI 保持选择、新版完整 Project 运行等仍由主控后续受控验证。初始 P2 事实、旧/新 SHA 和模型保留，不追改成旧版本原已验证隐藏类别。

**收尾口径澄清：2026-11-05 14:53:46 UTC / 22:53:46 +08:00。** 按主控要求仅追加本段，不新增测试、不改源码、不操作浏览器或 DB。

- 已确认的事实是：旧 Record 末端模板观察不到隐藏首部，不能单靠这张图证明首部也已选中；Home→Shift+End 的正常列表语义是全选。先前 P2 标签指完整性验证风险，不是已经独立复现了业务 UI 中的错误选择、Home 丢失或实际工程漏成员。输入失效模型只说明原 guard 的辨别能力，不冒充实际 RDP 故障。
- 用户要求的“受控操作＋DB 成员验收”应分别记录过程保护和最终结果。本 agent 对已有 DBX 文件重新作只读内容比较：原工程时间戳及 10 条成员未变，新工程为 12 条；与主控报告的预期字段/标签相符，因此没有依据把这些实际项目判为不完整。该判断是核对主控归档结果，不是独立执行 DB 验收。
- 初次 30 文件快照、补核的可见性限制及后续 32 文件保护修复各保留原 SHA/时间范围。当前报告未发现已确认的实际成员错误；隐藏首部这一证明缺口已在附记所述固定布局和定向模型范围内补强。后续用明确预期成员集合验收实际 Project，不能将单张末端图片的局限扩大成实际数据损坏结论，也不将现有样本推广到任意 Record/界面版本。
