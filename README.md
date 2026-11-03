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

这些入口**尚不是完整的新建操作，也不是 MCP 工具**：名称、类型、Record 字段、AE 的多个 Step 与各种 Action 的输入和保存、重名处理、保存后核验，以及 MCP 参数和调用接口均尚待实现与验证。Field 和 AE 对话框识别保护在首次实测后补充并各复测成功一次。不得把草稿打开成功视为对象已创建。

#### 空闲超时恢复与 GM 测试对象

2026-11-03 实际观察到 JumpServer“超过最大空闲时间120分钟，断开连接”，已由 Maa OCR 识别并关闭提示。Python 恢复入口另提供固定的刷新→识别资产连接页→使用浏览器已保存账号连接→检查 1920×1080 原始画布及 HRDEV 标题的流程；17:16 的真实退出再进入测试成功。恢复过程没有 AI 意图推理。`run_pipeline.py` 可在业务开始前触发恢复；业务执行中途失败不会自动重放。长期空闲后的完整恢复尚未再次等待验证，未覆盖 JumpServer 登录页或 MFA。

用户授权创建的 `GM_CX26_F1` Field 已保存并重新打开核对；`GM_CX26_R1` Derived/Work Record 已保存，包含该 Field，重连后仍显示该定义。AE 尚未创建，完整创建流水线仍待固化。每次运行可自动保存 Maa 原生截图、OCR 框、动作、耗时和成功/失败事件到本机忽略目录。操作表、截图、命令和验证边界见 [恢复与对象开发记录](psauto/docs/recovery.md)。

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
