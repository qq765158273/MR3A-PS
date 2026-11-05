<!-- markdownlint-disable MD033 MD041 -->

<div align="center">

<img src="assets/logo.png" alt="MR3A Logo" width="256" height="256"/>

# MR3A

《忍者必须死3》自动化助手。图像识别 + 模拟控制，解放双手。  
Powered by [MaaFramework](https://github.com/MaaXYZ/MaaFramework) & [MFAAvalonia](https://github.com/MaaXYZ/MFAAvalonia)

<a href="https://github.com/originalsage/MR3A" target="_blank"><strong>🔗 本项目 GitHub 仓库</strong></a>

</div>

<p align="center">
  <a href="https://github.com/originalsage/MR3A/releases"><img alt="release" src="https://img.shields.io/github/v/release/originalsage/MR3A"></a>
  <a href="LICENSE"><img alt="license" src="https://img.shields.io/github/license/originalsage/MR3A"></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows-blue">
</p>

## 使用须知

项目处于**快速迭代**阶段，偶发小问题欢迎反馈，我们会尽快处理。

- 问题反馈：[GitHub Issues](https://github.com/originalsage/MR3A/issues)
- 用户 QQ 交流群：**[1090310179](https://qm.qq.com/q/6gdcO5wvhS)**（使用答疑、功能建议、闲聊摸鱼，bug反馈，欢迎来玩~）

## 功能列表

### 日常任务

- ✅ **启动游戏** - 自动启动应用，处理常见弹窗；签到与限定结神符（支持多服/区服选择）
- ✅ **通灵巡逻** - 自动巡逻（可选：巡逻关卡）
- ✅ **竞技场** - 跑酷挂机；老板娘问答99%正确率
- ✅ **领取饭团** - 自动领取每日饭团
- ✅ **小屋修炼** - 忍者小屋修炼
- ✅ **忍村试炼** - 试炼关卡可配置；可选择保留包子数量
- ✅ **每日商店** - 自动购买（可选忍币购买神秘商店）
- ✅ **免费召唤** - 自动免费召唤（可选忍币召唤白银武库）
- ✅ **每日悬赏** - 好友/族员组队、抢 MVP 等（可配置邀请超时时间与开大延迟）
- ✅ **决胜狭路** - 决胜狭路玩法；不建议使用体验忍者
- ✅ **3v3（测试中）** - 仅支持困难图匹配（固定延时逻辑）
- ✅ **领取奖励** - 神龙契约、家族祈福、好友忍币、每周兑换码、领取邮件、忍阶任务、领取战令、活动奖励
- ✅ **关闭游戏** - 收尾关闭；多账号可复制任务组并分别选区服

### 常驻任务

- ✅ **周末活动** - 仅周末执行；支持光影忍法帖、忍界乱斗等
- ✅ **深渊挑战** - 周五限定；可选择挂机等待开启、自定义选卡时间
- ✅ **家族战** - 仅周末执行；可挂机等待开战、混团本
- ✅ **备战副本** - 挂机刷满每周备战
- ✅ **地区首领** - 自动刷满每日地区首领
- ✅ **S/SS+** - 召令悬赏刷 S / SS+（可分别开关）

### 限时活动

- ✅ **镜界百器** - 清体力、完成每日任务（可分别开关）
- ✅ **祈TA宠爱** - 需在对应活动页运行；可选祈福类型
- ✅ **万川修行** - 活动关卡流程；可选是否使用体验角色
- ✅ **幽狱永镇** - 活动关卡；可选难度
- ✅ **乐斗超级忍** - 活动关卡；可选运行模式、未开放时挂机等待
- ✅ **每日逆袭悬赏** - 刷逆袭 A（可配置刷每日一张/清空自己的/清空次数）
- ✅ **每周逆袭悬赏** - 可选择要刷的逆袭 boss
- ✅ **寻宝大冒险** - 可选运行方式一直刷或仅完成每日任务
- ✅ **神品传颂藏宝图** - 专刷神品，可选择地区页面或寻宝助力页面刷取
- ✅ **每日藏宝图** - 刷藏宝图（自选属性/是否刷自己的藏宝图等选项）

## 新手上路

### 使用文档

详细图文教程见 [新手上路](https://originalsage.github.io/MR3A/manual/newbie)。

### Windows

99.99% 的用户从 [Releases](https://github.com/originalsage/MR3A/releases/latest) 下载 `MR3A-win-x86_64-vxxx.zip`，解压后运行 `MR3A.exe`；搭配 **MuMu**、**雷电** 等模拟器使用。

### Android（手机端）

- 暂不支持。

### 使用前注意

1. 请在**游戏设置中关闭好友组队邀请**，避免任务被干扰。
2. 模拟器分辨率应为横屏 16:9 比例，推荐（以及最低）分辨率为 `1280x720`。
3. 新版本可在客户端设置中开启 GitHub 自动检测更新，或加入 [用户 QQ 群](#user-qq-group) 获取最新版本通知。

## 开发相关

更多说明请前往 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 主仓库查看。

### JumpServer / PSIDE 自动化验证

本仓库的 `psauto/` 是 JumpServer Web RDP 控制器的验证入口：通过 Playwright CLI 获取画面并发送输入，复用 MR3A 的 MaaFramework、AgentServer、自定义组件、OCR 模型和 Pipeline。目标环境仅限 PeopleSoft dev/test，当前开发基准为远程桌面 **1920×1080**。

截至 2026-11-03，已确认和验证：

- JumpServer 保存了 `1920×1080` 的 RDP 分辨率。当前 Guacamole 画布的逻辑有效区域为 `1920×1080`，底层 canvas 缓冲区为 `1920×1088`；多出的 8 行不能当作桌面内容。
- 同一远程画面会随浏览器空间缩放。人工全屏能改善观看，但自动化识别以原始画布为准；截图坐标必须按实际缩放比例换算为网页坐标。
- 曾对一张真实 PSIDE 截图做离线 OCR 比较：原图中选取的 6 个标题或菜单词均识别到，缩至约 `763×429` 的模拟预览中均未命中。小字的识别仍会变化，将标题区域裁剪并放大两倍后识别到了 `Application Designer`。这是单张截图的结果，不代表整体准确率。
- 已通过 Python → Playwright CLI → 已连接 Chrome → Maa 控制器获得实际 `1920×1080` 截图；模拟页面验证了缩放坐标、输入以及原 MR3A AgentServer 的自定义动作调用。
- 2026-11-03，`PSIDE_Demo` 在 HRDEV 实际窗口完成：Maa 内置 OCR 识别标题 → 原生按键节点发送 `Ctrl+O` → OCR 识别中文“打开定义” → 模板匹配并点击“取消”；最终截图确认返回主窗口。无对话框时，取消节点返回失败；模拟按键失败时，会尝试释放 Ctrl 并返回失败。另在对话框名称栏输入英文测试字符串并取消，未执行搜索或保存。

**尚未完成的验证**：以上仅是一个 HRDEV 会话中的可恢复示例，真实中文输入、CLI 本身断开后的恢复及长时间无人值守运行仍需测试；本机远程桌面断开后曾完成截图和上述示例，但不能据此保证长期持续刷新。原始截图支持已观察到的桌面 canvas，以及重连后额外出现的 64×64 小平移图层；分辨率、图层尺寸、数量或变换不符时停止。MR3A 现有界面仍配置为 ADB；CLI 控制器通过 Python 入口连接，尚未接入原 GUI 的控制器选择。

配置、运行和测试方法见 [psauto/README.md](psauto/README.md)。登录态、业务截图和临时诊断文件保存在 Git 忽略目录，不应提交。

#### PSIDE 新建操作探索

2026-11-03 在 HRDEV 以可取消的方式验证了 Field、Record 和 App Engine Program 的新建入口。`Ctrl+N` 打开 `New Definition`，选择对象后进入对应的未保存编辑页；Field 显示类型和长度，Record 显示字段和 Record Type，AE 默认有 `MAIN` 与 `Step01`。AE 中选中 Step 后，`Ctrl+3` 可插入 Action；现场看到了 SQL、PeopleCode、Do While、Do Select、Call Section、Log Message 和 Do Until 等选项。AE 的 `Ctrl+S` 打开 `Save As` 名称对话框，测试时已取消，未保存业务对象。

`assets/resource/pipeline/PSIDE/create_drafts.json` 中的 `PSIDE_OpenFieldDraft`、`PSIDE_OpenRecordDraft`、`PSIDE_OpenAEDraft` 是实验性的 Maa Pipeline 草稿入口，只负责打开未保存编辑页并识别结果，三个入口曾分别在该会话成功执行一次。运行前需要 PSIDE 处于空白主窗口；它们还没有自动检查所有窗口状态，不能在有人编辑其他对象时运行。PSIDE 会级联移动新建窗口，后续填写需要基于识别结果定位，不能假定编辑器始终处于固定坐标。

这些探索入口只打开草稿；正式创建与 MCP 能力见下文。Field 和 AE 对话框识别保护在首次实测后补充并各复测成功一次。不得把草稿打开成功视为对象已创建。

#### MCP 操作完成边界

2026-11-04 按用户要求，`create_field`、`create_record`、`create_ae` 的目标统一为：**执行创建与输入 → 识别保存成功 → 关闭该对象的编辑窗口 → 回到空白操作台**。保存后不重新打开对象，不读取并核对字段、类型、Step 或代码内容；对象是否正确写入由 DB 负责核对。界面定位、重名保护和保存反馈检查仍用于决定操作是否可以继续。

成功返回 `status: saved_and_closed`、`saved: true`、`workspace_ready: true`，表示界面操作已完成，不表示数据库内容校验通过。服务串行处理操作；保存后关闭失败时返回 `partial`，`workspace_ready: false`，并阻止该服务实例继续操作后续对象，直到检查操作台并重启服务。该结束流程已写入 JSON，三个工具均已通过完整真实创建调用。

#### dbx 独立验收进度

2026-11-04 的实测使用 dbx 的 `ps-dev / HRDEV` 连接只读验收；创建和 Build 仍通过 PSIDE 的 Maa Pipeline 执行。`GM_MCP_EMPLID` 已保存并关闭，dbx 确认 Character、长度 11。`GM_MCP_REC` 已保存、Build 并关闭；五字段顺序正确，前三个 Key/Search Key/Listbox，后两个非 Key 的 Alternate Search Key/Listbox，物理表位于 `HRAPP`、三个索引有效、当前行数 0。`GM_MCP_AE` 也已保存并关闭；dbx 确认 Step01 的 COUNT SQL、Step02 循环读取字段名的 PeopleCode 及编译长度 564。目标对象均经分段校准完成，不能把此前完整 MCP 失败改计成功；补测 REC2 也属分段完成。

模板迁移后已跑通完整 MCP 链路，并由 dbx 只读验收：

原始 1920×1080 画面与来源见 [验收截图](psauto/docs/images/acceptance-20261104/README.md)。

| 能力 | 本轮完整调用与结果 |
| --- | --- |
| Field | `GM_MCP_FLD12`、`GM_MCP_FLD13` 在同一会话连续从头成功，各约 284 秒；Character、长度 11、标签参数均正确 |
| 重名保护 | 重复 Field13 返回 `already_exists`，关闭对象并释放操作台，约 115 秒 |
| Record / Build | 空白操作台主动断开后，MCP 自动重连，再从头创建及 Build `GM_MCP_REC3`，约 997 秒；五字段和属性正确，HRAPP 表、三个有效索引、行数 0 |
| 复选框补强后的 Record | `GM_MCP_REC4` 完整创建、Build、关闭通过；226 个节点、12 次点击后状态确认全部通过，DBX 确认五字段属性、HRAPP、三个有效索引及 0 行；含证据导出约 972 秒，见 [本轮截图与 DBX 结果](psauto/docs/images/acceptance-record4-20261104/README.md) |
| AE | 同一会话随后从头创建 `GM_MCP_AE3`，约 516 秒；Step01 COUNT SQL 指向 REC3，Step02 PeopleCode 循环字段名，源码及编译长度 566 通过 dbx；已保存并关闭 |
| 四步 AE | `GM_MCP_AE4` 从头创建约 816 秒，保存关闭并释放操作台；dbx 确认 MAIN 下 Step01–04 顺序及 SQL/PeopleCode/SQL/PeopleCode 类型，两个 COUNT SQL 正确，两段 PeopleCode 源码正确且编译长度均为 566 |

`GM_MCP_FLD11` 较早的一次完整调用也成功；前面的失败和分段校准不会改计成功。AE 仅完成创建和保存，未执行程序。开发机此前完整回归 52 项通过；本轮相关参数/服务/MCP 12 项、原生图像 3 项、剪贴板/连接 5 项及 schema 通过。这些是当前基准上的样本，尚不代表跨 DPI 或长期无人值守验收。参数、失败记录和最新结果见 [MCP 与 dbx 实测记录](psauto/docs/acceptance.md)。

实测确认：隐藏 Chrome 下关闭 JumpServer 剪贴板时，需要完成网页抽屉的离场动画，再恢复远程输入焦点。原始 canvas 截图不能显示网页遮挡，不能绕过点击遮挡检查。查重结果中的零计数曾被整段 OCR 漏掉；随后整段模板也在更强的 10/100 合成反例中暴露子串误判，现改为只匹配计数首位的数字 0。Field 类型下拉框必须明确提交并关闭，再操作长度；长度值不再 OCR 回读，避免光标被读作额外的数字，最终由 dbx 验收。

#### 当前完整配置与性能（2026-11-05）

证据导出已改为通过 Maa 公开接口逐节点读取、写图后释放，减少像素复制；原生日志、失败候选及无损截图全部保留。208 节点离线原生对照中，Python 导出进程的新增 private 峰值从 2.43 GiB 降至 24.85 MiB，导出从 24.889 秒降至 22.380 秒；208 节点、1664 事件及 99 张 PNG 的非计时内容和像素一致。主要收益是内存，单次约 10% 的导出耗时改善不代表整体业务提速。既有 `timings.json` 新增取详情、哈希、转换、PNG 编码/写盘分项，保留业务事实与证据故障隔离。方法、原始测量及验证边界见 [证据导出优化](psauto/docs/performance/evidence_export.md)。

本轮新 MCP 实例完整创建 GM_EXP_REC、Build、保存关闭及 DBX 验收通过，208 节点无重试或动作失败，全部证据保留。现场总耗时 230.34 秒、导出 27.565 秒，高于此前样本；执行阶段截图和输入调用已明显变慢，不将此次作为业务提速证据。截图、原生分项及差异见 [真实接入验收](psauto/docs/images/acceptance-export-20261105/README.md)。

现有 tmux pshelp 完成本轮独立只读复核：核心导出与故障隔离通过，发现的采样线程异常漏报已修复并独立复验；主控已完整读取[正式报告](psauto/docs/performance/pshelp_export_review.md)，18 个审核文件 SHA 均一致。普通套件 52 通过、57 项集成测试跳过；最终 benchmark 正常路径及采样异常不发布指标也由主控以原生 Maa 补测通过。未证明长期成功率；下一轮优先定位现场截图/输入调用的耗时波动，再按详情读取、编码和哈希分项评估导出成本。

后续独立审核指出的三个既有问题已修复：Build 计数按完整数字判决；业务保存/关闭事实与证据写入状态分离；恢复探针、控制器及事件订阅清理补齐。证据或操作异常保留已知业务结果，同时 next_operation_allowed=false 阻止下一任务，不重放。pshelp 对最终 9 个文件哈希复核通过其离线/故障模拟范围；服务 20 项、恢复 9 项、原生识图 12 项通过，另以最终代码完整创建 GM_FIX_FLD 并经 DBX 验收。接口及边界见 [可靠性修复](psauto/docs/reliability_fixes.md)、[正式复核](psauto/docs/pshelp_reliability_review.md) 和 [真实补测](psauto/docs/images/acceptance-review-fixes-20261105/README.md)。

官方 CLI 配置 `timeouts.settle=0` 已完成隔离对照及真实浏览器验证，并在同一 MCP 服务实例连续完成四次完整调用，共约 **6 分 21 秒、409 个节点**，全部保存关闭、释放空白操作台，0 识别轮次重试、0 节点失败、0 动作失败；DBX 全部通过。Pipeline 的节点和业务缓冲保持，最终 Step 身份边界补丁也已完成本轮四步 AE 回归。

| 操作 | 历史完整调用 | 本轮工具调用含导出 |
| --- | ---: | ---: |
| Character 长度 11 | 133 秒 | **47 秒** |
| Date | 120 秒 | **43 秒** |
| 五字段 Record＋Build | 524 秒 | **170 秒** |
| 四步 AE | 353 秒 | **120 秒** |

历史值包含各自进程启动，本轮为同一 MCP 实例的连续工具调用；原生 Maa 事件跨度也分别从 120/108/493/326 秒降至 40/37/145/101 秒。同一后台 Chrome、同一原图的只读对照中，截图含解码中位数从 1046ms 降至 180ms。官方 CLI 的通用等待在页面内使用 setTimeout，默认 500ms 还会受到后台调度影响；本轮通过官方配置减少这层等待，没有修改安装中的 CLI 源码。

本机直接附加到已绑定浏览器 `psauto-discovery`，创建 `psauto-fast` 调用会话，复用现有 Chrome 授权；底层浏览器会话保持运行。项目连接配置指定 `cli_settle_ms:0`，客户端启动时读取官方实际配置，不匹配就拒绝提交输入；四个任务均记录了预期和实际 0ms。配置只在 CLI daemon 启动时加载，不能给单条命令加参数后假定生效。配置、完整数字和限制见 [本轮配置与性能](psauto/docs/performance/settle_optimization.md)，原始截图、DBX 及逐节点日志见 [完整验收](psauto/docs/images/acceptance-settle0-20261105/README.md)。长期稳定性仍需积累运行样本。

#### Record 历史性能分析与后续优化

GM_MCP_REC4 实际完成 226 个节点，Pipeline 约 906 秒：截图及下一轮准备约 532 秒、控制器输入约 238 秒、动作前后延迟约 102 秒、全部识别约 29 秒、引擎起始约 4 秒。20 次候选识别未命中均为正常分支，无动作失败或重试循环。另有约 66 秒用于启动、证据导出和最终返回。当前瓶颈是 CLI 调用及节点粒度；Ctrl+Enter 拆分三步就分配约 14 秒，不能用“每步延迟 1 秒”估算整条流程。

优化前隐藏浏览器的只读补测中，CLI 空命令约 2 秒；473 张导出 PNG 只有 107 种不同内容。随后实现官方 CLI 客户端常驻、Record 组合键、延迟调整与证据去重，并完整创建、Build、关闭 GM_MCP_REC7，DBX 六项验收通过。总耗时从 **16 分 12 秒降至 8 分 44 秒，减少约 46%**；Pipeline 从 906 秒降至 493 秒，12 次复选框点击后确认全部通过，89 个 DoNothing 检查保留。节点数 226→208，PNG 文件 473→110，判决仍使用实时原始截图。当前最大开销仍在后台截图，单次传输中位数约 1.656 秒。Field/AE 也已迁移相同策略；四步 AE5 从约 816 秒降至约 353 秒，Field14 从约 284 秒降至约 142 秒，均经 DBX 内容验收。见 [AE5 验收](psauto/docs/images/acceptance-ae5-20261105/README.md) 和 [Field14 验收](psauto/docs/images/acceptance-field14-20261105/README.md)。

名称检查补齐了输入后移开光标，降低光标对末位数字的干扰；保存标题/OK 复用固定图片，Build 名称检查缩到单行。这些校准失败与分段结果仍单列，不计完整成功。优化实现、前后对比、208 行耗时 CSV 和截图见 [执行链路优化](psauto/docs/performance/optimization.md)；原始诊断口径及 [226 行基准耗时](psauto/docs/performance/record4_nodes.csv) 见 [性能分析](psauto/docs/performance/README.md)。

每次运行的 `events.json`、`report.json`、`summary.json` 和 `timings.json` 都由同一条 Maa/MR3A Pipeline 事件链生成；其中 `summary.json` 自动记录节点成败和阶段耗时，CSV 只是跨运行对照材料。

2026-11-05 补强：汇总按原生 task/node ID 对应节点，包含失败节点和识别重试；同名节点及嵌套任务不会按列表位置错配或重复统计。`candidate_misses`、`scan_retries`、`pipeline_node_failures` 和 `action_failures` 分开报告，反向识别的原始 hit=false 由 `rule_passed` 表达真实规则判决。4 份真实日志回放和原生 Maa 重试/失败测试通过。Field/AE 的查重及保存顺序修正为输入后先 Tab 移开光标，再识别名称。

用户切到浏览器全屏后，远程原图仍为 1920×1080，浏览器视口变为 1920×1024，页面可见。Field15 完整调用约 92 秒、45 个节点计时齐全且 DBX 通过；此时原始截图实测约 594–600ms。该结果包含浏览器可见性变化，不能全算作代码提速。截图、自动 summary 和 DBX 返回值见 [Field15 验收](psauto/docs/images/acceptance-field15-20261105/README.md)。

2026-11-05 再次复核原生日志：REC7 的 20 次候选未命中是正常分支，实际没有识别重试或动作失败。AE 将同一标题的对象名/Step 合为一次 `1100×24` OCR，Dirty 检查通过后直接 Ctrl+S；Field 合并连续按键及重复标签检查，保留全部保存反馈和关闭后空白台判决。完整四步 `GM_AE_FAST` 为 124 个节点、约 353 秒，Character `GM_AUDIT_F` 为 40 个节点、约 133 秒，Date `GM_AUDIT_DATE` 为 37 个节点、约 120 秒，均保存关闭并经 DBX 验收，三次均无识别轮次重试或动作失败。AE 总耗时与上次接近，不能说此次显著提速。

截图分项实测：Guacamole 本地绘图队列刷新约 18–21ms，原画布读取和编码约 47–50ms，完整 CLI 请求却约 932–1001ms；Python 解码另约 44–70ms。原画布不是主要瓶颈，官方 CLI `run-code` 包含默认 500ms 的 settle 等待，剩余成本还在执行链路及返回。默认 `canvas_refresh_mode:guacamole` 在截图前排空已接收绘图队列，缺组件/API、超时、尺寸变化或断线即停止；这不保证网络端新帧，下一步仍由 Pipeline 状态识别判断。剪贴板抽屉继续使用浏览器动画刷新及遮挡检查，最终 Ctrl+V 前重查连接。

部分对象 `GM_AE_BASE` 的后台浏览器截图超时仍保留为失败样本，不重放、不计完整成功。只读复核发现的对象名左边界及缺组件回退问题已补强。随后通过 tmux pshelp 内的 `seedx codex` 完成独立复核并回复 ps：原始证据和性能数字一致，未发现高风险问题，另发现 Step 标识符边界缺口。该问题已修复，新增错误 Step 下不发送 Ctrl+S 的原生 Pipeline 反例，识图 10 项和参数/schema 6 项通过；随后的 0ms 配置完整回归已补齐最终版本四步 AE 验证，长期稳定性仍待积累。正式反馈及处理见 [pshelp 独立复核](psauto/docs/performance/pshelp_review.md)；此前逐项取舍、截图分解和原生逐节点日志见 [Pipeline 复核](psauto/docs/performance/pipeline_audit.md) 及 [本轮截图和 DBX](psauto/docs/images/acceptance-pipeline-audit-20261105/README.md)。

本机启动复核 agent 应使用 `seedx codex`，其提供正确的模型与网关授权；全部 `-c` 配置覆盖放在 `exec` 之前，保留 seedx 的网关注入，避免子命令配置覆盖后退回本机旧 provider。此前直接启动全局 Codex 的 401 不代表 seedx agent 不可用。

#### 截图和 OCR 区域基准

2026-11-04 已用现有真实截图对比 Maa 原生 OCR 与模板。按用户偏好，固定控件优先局部模板，普通模板阈值为 **0.85**；动态对象名和字段名保留必要的局部 OCR。零计数现只看 `[696,719,7,11]` 的首位数字，并确认对话框图片；8 张真实帧及 10/100 合成反例中，数字 OCR 和数字模板均符合预期，模板约 18–20ms、OCR 约 37–45ms，因此当前选数字模板。三个创建 JSON 的查重静态控件已迁移，50 项实际 JSON 离线识别检查通过。Key 模板需覆盖普通与悬停样式，模拟放大 125% 后原尺寸模板失效，分辨率和 DPI 仍需固定。样本、计时和局部示意图见 [截图识别方法对比](psauto/docs/recognition_comparison.md)，这些小样本结果不代表整体准确率或长期稳定性。

进一步发现 Step02 整段模板与 Step01 的相似度约 0.891，故不能只用 0.85 判断步骤身份。Step01/02 按分数选择候选，再检查末位编号小图；Step03/04 通过新动作图标定位后，局部 OCR 严格检查 Step 名，四步 AE 已实测。复选框整框对未勾选的分数约 0.852，同样不适合直接降到 0.85；当前保持 0.97。点击后在同一个 13×13 框内确认目标状态，覆盖普通与悬停样式，未生效即停止，不重试切换。12 组真实前后帧回放及未变化反例通过；随后 GM_MCP_REC4 完整创建、Build 和关闭也已通过，12 次点击后确认全部命中，DBX 属性核验正确。内部 9×9 勾形方案仍保留为未提交试验。

每个卡点的识图/文字 OCR 选择、局部区域、动作延迟、下一步判决和失败处理，统一记入 [卡点与判决表](psauto/docs/recognition_decisions.md)。已确认禁用 SQL 菜单仍能得到约 0.999 的文字图片相似度，因此“出现菜单项”不代表“可以打开”；新增动作行选中背景与菜单启用颜色检查。重试只覆盖粘贴前的幂等选择与菜单操作，最多一次；保存和 Build 不盲目重放。Maa 的 timeout 控制当前节点等待 next，保存/Build 的 30/60 秒等待已放在对应动作后。

业务识别使用原始 `1920×1080` 远程桌面截图；OCR 在 Pipeline JSON 的 `roi` 内执行，完整截图留作证据。浏览器显示缩放不改变这套远程坐标。JumpServer 超时提示属于浏览器页面，使用浏览器截图坐标，不能套用远程桌面坐标；没有 RDP canvas 时仍能用 Playwright 截取浏览器页面。

| 场景 | 应识别的局部范围 | 通过条件 |
| --- | --- | --- |
| 主窗口/对象标题 | 主窗口 `1100×70`，AE 代码编辑器身份 `1100×24` | HRDEV、预期对象名/编辑器类型；AE 还要求精确 Step |
| 打开定义/查重 | 对话框标题、类型框、名称框、结果栏分别识别 | 对象类型正确、名称正确、明确找到或明确 0 条 |
| 下拉菜单 | 仅展开后的菜单；当前定义类型菜单 `190×330` | 目标项匹配，选择后再检查类型框 |
| Field | 类型和长度各一行、标签表格的目标行 | 用于保存前定位输入控件；保存后关闭，内容由 DB 核对 |
| Record | 字段列表的名称列、类型单选项 | 用于插入字段和选择类型；保存后关闭，内容由 DB 核对 |
| AE 结构 | MAIN/目标 Step、该 Step 的 Action 类型 | 用于定位当前 Step 的代码编辑器；最后保存并关闭，内容由 DB 核对 |
| 代码保存 | 保存图标 `32×32` 模板匹配、编辑器活动状态；PeopleCode 底部 `650×25` OCR | 修改后出现待保存状态，Ctrl+S 后恢复已保存状态；代码正文不做 OCR |
| 断开/异常 | 浏览器中央提示框或 PSIDE 当前模态框 | 已知提示才进入对应 JSON 分支；未知错误停止 |

2026-11-04 对同一张真实截图做 Maa 原生 OCR 离线比较：类型框旧 ROI `[775,375,190,25]` 将 `Field` 识别为 `Freld`；保留上下边距并排除箭头的 `[770,368,168,38]` 正确识别为 `Field`。固定单行内部区域配合 Maa `only_rec` 也通过。ROI 应覆盖完整文字并留边距，不能一味缩小或放宽匹配表达式。此结果只证明该截图中的区域校准，不代表完整创建流程已经通过。

详细坐标、当前实现与待收窄范围、识别框示意图见 [截图与 OCR 场景约定](psauto/docs/recognition.md)。编辑器当前仍有 `[430,75,1100,730]` 的大范围 OCR，后续应改成一次定位锚点、后续引用锚点的小 ROI；不把它作为已经优化完成的流程。

#### 空闲超时恢复与 GM 测试对象

2026-11-03 实际观察到 JumpServer“超过最大空闲时间120分钟，断开连接”，已由 Maa OCR 识别并关闭提示。Python 恢复入口另提供固定的刷新→识别资产连接页→使用浏览器已保存账号连接→检查 1920×1080 原始画布及 HRDEV 标题的流程；17:16 的真实退出再进入测试成功。恢复过程没有 AI 意图推理。`run_pipeline.py` 可在业务开始前触发恢复；业务执行中途失败不会自动重放。长期空闲后的完整恢复尚未再次等待验证，未覆盖 JumpServer 登录页或 MFA。

用户授权创建的 `GM_CX26_F1` Field 已保存并重新打开核对；`GM_CX26_R1` Derived/Work Record 已保存，包含该 Field，重连后仍显示该定义。`GM_CX26_A1` AE 的开发试验已保存 SQL 和 PeopleCode，代码采用远程剪贴板粘贴；这不代表完整参数化创建流水线已通过。AE 当前只支持 SQL 与 PeopleCode 方向。2026-11-04 的 `GM_MCP_F1` MCP 创建尝试仍停在查重阶段，未保存新对象；随后只读复测通过了修正 ROI 的类型检查。每次运行可自动保存 Maa 原生截图、OCR 框、动作、耗时和成功/失败事件到本机忽略目录。操作表、截图、命令和验证边界见 [恢复与对象开发记录](psauto/docs/recovery.md)。

## 致谢

### 核心框架

- [MaaFramework](https://github.com/MaaXYZ/MaaFramework) — 基于图像识别的自动化框架
- [MFAAvalonia](https://github.com/MaaXYZ/MFAAvalonia) — Maa 通用 GUI

### 贡献者

感谢以下开发者对本项目的贡献:

[![Contributors](https://contrib.rocks/image?repo=originalsage/MR3A&max=1000)](https://github.com/originalsage/MR3A/graphs/contributors)

## Star History

<a href="https://www.star-history.com/?repos=originalsage%2FMR3A&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=originalsage/MR3A&type=date&theme=dark&legend=top-left&sealed_token=6ndcRocJekpnM7IWch5wBulkGU0gucRUXK09jImopG5P_lqOY1C8Y2IPerlRDbOO4YVOFwc0DMZJp7kBZReqnnZZvWDXx6XXrm9EgJ-O_saY0pOuBhl-KQ" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=originalsage/MR3A&type=date&legend=top-left&sealed_token=6ndcRocJekpnM7IWch5wBulkGU0gucRUXK09jImopG5P_lqOY1C8Y2IPerlRDbOO4YVOFwc0DMZJp7kBZReqnnZZvWDXx6XXrm9EgJ-O_saY0pOuBhl-KQ" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=originalsage/MR3A&type=date&legend=top-left&sealed_token=6ndcRocJekpnM7IWch5wBulkGU0gucRUXK09jImopG5P_lqOY1C8Y2IPerlRDbOO4YVOFwc0DMZJp7kBZReqnnZZvWDXx6XXrm9EgJ-O_saY0pOuBhl-KQ" />
 </picture>
</a>

---

<a id="user-qq-group"></a>

<div align="center">

🌟 如果你觉得本项目有帮助，请点个 ⭐ Star 支持一下❤️！

MR3A 用户 QQ 交流群：[1090310179](https://qm.qq.com/q/6gdcO5wvhS)

本项目采用 [AGPL-3.0](LICENSE) 许可证

</div>
