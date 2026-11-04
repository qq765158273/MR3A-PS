# PSIDE MCP 实测与 dbx 验收

创建操作使用 Maa 原生 Pipeline 和 Playwright CLI，数据库只读查询使用 dbx 的 `ps-dev / HRDEV`。DB 查询用于开发验收，不加入 MCP 创建流程。MCP 结束于保存、关闭、释放空白操作台，不重新打开核对对象。

已提交的原始截图及来源见 [验收截图](images/acceptance-20261104/README.md)，包含 Field、Record 属性及 Build、四步 AE 和最终空白操作台。

## 当前结果

完整 MCP 验收已完成下列样本；成功均表示保存、关闭并回到空白操作台，DBX 独立核验内容。AE 未执行。

| 完整调用 | 用时 | MCP 与 DBX 结果 | 本机证据 |
| --- | --- | --- | --- |
| Field12、Field13 | 各约 284 秒 | 连续创建成功；Character、长度 11、标签参数正确 | `out/template_acceptance_results3.json` |
| 重复 Field13 | 约 115 秒 | `already_exists, workspace_ready:true`，无覆盖 | 同上 |
| `GM_MCP_REC3` | 996.62 秒 | 新任务前主动断线，MCP 自动恢复后首次完整创建及 Build；五字段及属性正确，HRAPP 表、三个 VALID 索引、行数 0 | `out/objects/20261104_164647_935317/` |
| `GM_MCP_AE3` | 515.99 秒 | 同一会话随后完整创建；SQL 指向 REC3，PeopleCode 源码正确、编译长度 566 | `out/objects/20261104_170324_644760/` |
| `GM_MCP_REC4` | 约 972 秒（含证据导出） | 复选框补强后完整创建、Build、关闭；226 个节点，12 次点击后确认全部通过；DBX 确认五字段及属性、HRAPP、三个 VALID 索引、0 行 | `out/objects/20261104_183010_506938/` |
| `GM_MCP_REC7` | 524.384 秒（含启动、导出、返回） | 性能优化后完整创建、Build、关闭；208 个节点，12 次点击后确认通过；DBX 确认五字段属性、HRAPP、三个 VALID 索引、0 行 | `out/objects/20261104_205229_380875/` |
| `GM_MCP_AE4` | 816.42 秒 | MAIN/Step01–04，顺序 1–4，动作 S/P/S/P；Step01/03 为 `SELECT COUNT(*) FROM PS_GM_MCP_REC3`，Step02/04 循环读取字段名，源码正确且编译长度均为 566 | `out/objects/20261104_171343_260521/` |

REC3 与 AE3 的完整返回值见 `out/record3_ae3_recovery_results.json`；AE4 见 `out/ae4_four_steps_results.json`。这些成功不替换下方保留的失败与分段校准记录。未增加无关的对象回开核对流程。

最终审查补上了 Record 的点击后状态检查：原先识别未选中后点击会直接进入下一标签，现在必须在本次点击的 13×13 框内看到目标状态，模板覆盖普通/悬停样式，保持 0.97 阈值。12 组 REC3 真实前后帧，以及每组“点击返回成功但画面未变”反例，全部通过原生 Maa 回放；另外 3 条反向分支复用真实取消勾选像素验证，共 30 个任务。没有重复切换，失败不能进入下一属性。随后在 GM_MCP_REC4 的完整调用中，12 次点击后确认全部通过，Build 和关闭完成，DBX 确认属性、物理表及索引正确。Maa 任务事件跨度约 906 秒，含启动及证据导出约 972 秒；[本轮截图与六项 DBX 查询实际返回值](images/acceptance-record4-20261104/README.md) 已入库。

最终相关参数/服务/MCP 回归 12 项、原生图像回归 3 项、此前剪贴板/连接集成 5 项通过；完整本机回归较早为 52 项通过。当前样本不构成长期成功率统计。

性能优化后的相关回归为参数/服务/基础/传输/证据/MCP 19 项、CLI 集成 7 项、剪贴板/连接 5 项、原生图像 5 项及 schema 通过。REC7 的完整耗时比 REC4 减少约 46%，全部必要检查及 DBX 验收通过，[本轮截图和数据库返回值](images/acceptance-record7-20261104/README.md) 已入库。[优化记录](performance/optimization.md) 保留 REC5/REC6 校准失败、分段收尾与所有证据目录，不计为完整成功。

GM_MCP_REC4 的完整成功之前，一轮测试进程在查重类型确认后中断，未生成完成结果。DBX 确认定义不存在，随后用已有取消查重 Pipeline 并检查空白操作台，再新开完整调用。中断目录 `out/objects/20261104_175655_634418/` 和 `out/record4_interrupted.json` 保留，不计成功；取消窗口证据为 `out/runs/20261104_182955_594013/`。

## 开发校准与失败记录

以下按开发时的进度保留，涉及“当前”“正在”“尚未”的表述只代表该次记录时的状态；最新结果以上表为准。

目标 Field、Record/Build、AE 均已保存并关闭，分别经 dbx 验收。完成过程包含分段校准，完整调用失败仍保留，不计为成功。AE 最终的 Step01 SQL 是 `SELECT COUNT(*) FROM PS_GM_MCP_REC`；Step02 PeopleCode 源码完整，PSPCMPROG.PROGLEN=564。开发中一次 Step01/Step02 图片误选触发了删除关联 SQL 提示，已取消；之后 dbx 再次确认原 Step01 SQL 保留，Step02 的 PeopleCode 另行保存。

模板迁移后，`GM_MCP_FLD11` 的完整 `create_field` 已返回 `saved_and_closed, workspace_ready:true`，约 286 秒；dbx 确认 FIELDTYPE=0、LENGTH=11。证据为 `out/objects/20261104_145307_807222/`，连续调用结果存于 `out/template_acceptance_results.json`。后续 Field、重复名称、新 AE、新 Record/Build 仍在同一 MCP 会话顺序测试。

连续测试的第二个 Field 暴露了点击边界：Field 的 OCR 框为 `[809,599,26,14]`，第一次点击在 `(815,609)` 正确，第二次在 `(830,600)` 落入相邻 Component Interface 行。该调用在编辑器检查时停止，约 154 秒，未保存。已取消来源选择窗口，确认空白操作台。新建类型选择现使用 Home 后按 F/R 或向下三次，再用选中行图片确认类型，最后回车；不再点击类型文字框。

随后 `template_acceptance_results2.json` 的 Field12 在 Label ID 被 OCR 读成 `Label1D` 时停止，约 211 秒，未保存。已丢弃仅属于本次调用的 Field8 草稿并确认空白操作台。Field 编辑页的类型/长度标签、三个表头和 Save As/OK 已改为 0.85 截图模板；对失败帧的五个编辑标签均命中，Save As/OK 在该非保存页面被拒绝。下一轮结果写入 `out/template_acceptance_results3.json`，包括 Field12、Field13、重复 Field13、AE2、Record3。

该轮 Field12 与 Field13 已连续从头成功，各约 284 秒，返回 `saved_and_closed, workspace_ready:true`。证据分别为 `out/objects/20261104_151556_155315/`、`20261104_152040_039740/`。dbx 对目标 EMPLID 及三个补测 Field 的检查均为 Character、长度 11；PSDBFLDLABL 也确认 Label ID=GMEMPLID、Long Name=`GM MCP Employee ID`、Short Name=`GM Employee`、DEFAULT_LABEL=1，参数没有落到相邻列。Field 流程与参数绑定已作为可信进展提交 `ae7ca57`；MCP 其余流程仍待本轮完整结果。

## 本次请求

| 对象 | 参数 |
| --- | --- |
| Field `GM_MCP_EMPLID` | Character，长度 11 |
| Record `GM_MCP_REC` | SQL Table，依次加入 GM_MCP_EMPLID、EMPLID、EMPL_RCD、EFFDT、EFFSEQ；前三个 Key + Search Key + List Box Item；后两个保持非 Key，使用 Alternate Search Key + List Box Item；Build 物理表及索引 |
| AE `GM_MCP_AE` | MAIN/Step01 SQL：`SELECT COUNT(*) FROM PS_GM_MCP_REC`；MAIN/Step02 PeopleCode：按 FIELDNUM 查询 PSRECFIELD 的字段名并循环 MessageBox 打印 |

PeopleSoft 普通 Search Key 只在 Key 字段上可用。非 Key 字段应使用 Alternate Search Key；MCP 参数拒绝 `key:false, search_key:true`，避免默默忽略禁用选项。

## 已确认的开发校准

Field 已保存并关闭。dbx 只读查询返回 `PSDBFIELD.FIELDTYPE=0`、`LENGTH=11`，更新时间为 2026-11-04 11:33。开发中经过分段恢复，尚不能当作该名称从头创建的完整 MCP 稳定性证明。

另建 `GM_PIPE_REC` 作为流程校准对象，同样五个字段。dbx 检查 PSRECFIELD：前三个 USEEDIT=8390689，后两个 USEEDIT=8388656。位值对应 Key=1、Listbox=32、Alternate Search Key=16、Search Key=2048。前三个 Key/Search/Listbox 均设置，后两个为非 Key 的 Alternate Search/Listbox。

该校准 Record 的类型 RECTYPE=0，FIELDCOUNT=5。通过 PSIDE Build 后，dbx 确认 `PS_GM_PIPE_REC` 物理表存在且 TABLESPACE_NAME=HRAPP。PSIDE 输出窗口显示处理 1 个 Record、0 错误、0 警告。该对象只作校准，不替代目标 `GM_MCP_REC` 的完整 MCP 调用。

## 固化的界面行为

- 复用 JumpServer 远程剪贴板后，关闭抽屉并通过 Playwright 完成离场动画，再恢复远程键盘输入焦点；透明网页层也会拦截鼠标，不能放宽遮挡检查。
- 查重结果的 `0` 在 OCR 中不稳定，使用小区域的“0 已找到定义”模板。两张真实截图通过，数字替换为 1 和 10 的负例不通过。
- 名称输入的点击框限制在控件内部，避开上沿。识别文字框内的任意点击点不一定落在输入控件内部。
- 类型下拉框选择后必须明确提交，菜单关闭后才可输入长度；长度内容由 dbx 验收，避免 OCR 将光标当作数字。
- Insert Field 搜索是前缀匹配。单一结果会自动插入；多个结果需要选择准确名称行并再点 Insert。后续列表检查只看 Field Name 列，并使用完整名称匹配，避免把 GM_MCP_EMPLID 当作 EMPLID。
- Record Field Properties 用 Ctrl+Enter；Alt+Enter 打开的是 Record Properties。不同字段类型的属性布局不同，以 Keys 标题定位，再查找各选项的文字和旁边复选框。
- 使用 MR3A 原有 NodeOverride 组件绑定当前字段和属性分支；Python 只绑定参数，不执行字段属性操作循环。
- SQL Table 首次保存需要选择 PeopleSoft 表空间。当前 HRDEV 使用已存在的 HRAPP；参数 `tablespace` 指定目标，不能把 Oracle 默认表空间等同于 PeopleSoft 的已分配空间。
- Build 只针对当前定义，Create Tables 和 Create Indexes，Execute SQL now；表已存在时跳过，不选择 Recreate/Alter/View/Trigger。PSIDE 的旧日志路径可能已失效，使用输出窗口记录结果。
- Build 后焦点在输出面板，需先聚焦对象窗口，再 Ctrl+F4；最终空白操作台检查通过才放行下一任务。
- 隐藏 Chrome 中直接读取 canvas 可能仍得到上一帧。截图通道先通过 Playwright 刷新浏览器帧，再读取原始尺寸画布；浏览器截图只用于刷新网页渲染，不替代原图做 OCR。

## 实测状态

正在同一个 stdio MCP 会话连续调用重名 Field、目标 Record 和目标 AE。完整调用结果、数据库验收与运行次数将在各步骤完成后追加。当前不能宣布整套稳定性通过。

已完成：重名 `GM_MCP_EMPLID` 返回 `already_exists`、`workspace_ready:true`，用时约 115 秒；没有覆盖定义。同一 MCP 会话随后继续创建目标 Record。开发机完整回归 52 项全部通过，包含独立临时浏览器的真实 Maa OCR、剪贴板离场动画、坐标和恢复测试；这组回归不等同于 HRDEV 长期运行验收。剪贴板通道修复已独立提交，业务流程试验继续保留未提交。

第一次目标 Record 的完整调用在类型页切换后停止，返回 `saved:false, workspace_ready:false, built:false`，用时约 749 秒。截图确认隐藏 Chrome 存在上一帧画布读取问题；字段和属性步骤完成但不能据此判定对象已保存。已取消仅属于本次运行的未保存 Record5 草稿，确认空白操作台，再以刷新帧后的截图通道从头重试。该次失败保留在 `out/acceptance_results2.json`，不得计入成功率。

第二次完整 Record 调用通过了类型页切换，但 OCR 将 SQL Table 读成 SOL Table，仍按失败返回（约 779 秒）。已改为基于 Record Type 分组标题点击固定相对位置的选项，模板检查单选圆点，保存后由 dbx 核对 RECTYPE。当前目标 `GM_MCP_REC` 已通过修正后的剩余节点完成保存、Build 和关闭；dbx 确认 RECTYPE=0、FIELDCOUNT=5、字段属性正确、`PS_GM_MCP_REC` 位于 HRAPP，行数为 0。目标 Record 的完成属于分段校准后的完成，不能把前两次 MCP 失败改记为成功。

正在以新名称 `GM_MCP_REC2` 和完全相同的五字段属性从头执行完整 MCP 创建及 Build，之后同一会话创建 `GM_MCP_AE`。该 Record 是稳定性验收用的额外 GM 对象，不替代目标 Record。

`GM_MCP_REC2` 的首次完整调用又暴露了点击区域的尺寸边界：OCR 标题框高 14 像素，原高度偏移 -14 将点击高度减为零，Maa 拒绝动作，未保存。已将偏移改为保留正高度，并以两个实际截图及事件中测得的 14 像素框，运行真正的 Maa 识别和点击计算离线复测；三种尺寸均返回成功，点击点位于 SQL Table 行内。该失败同样保留，不能算完整调用通过。当前先完成该补测 Record 并创建目标 AE，随后再跑新名称的完整调用。

补测 Record `GM_MCP_REC2` 已在修正后的后续节点保存、Build 并关闭，dbx 确认其定义及物理表都存在。AE 的第一次完整调用在初始编辑页因为 MAIN 被大范围 OCR 读成 HAIN 而停止，尚未保存；改为 Section 表头 + Step01 的页面识别，MAIN 名称交 dbx 验收。已取消仅属于这次调用的 App Engine Program5 草稿并确认操作台空闲，重跑目标 AE 完整调用。

原始证据保存在本机忽略目录 `psauto/out/`，包括每次参数、Maa 事件、截图、失败节点和 MCP 返回值。失败尝试不会被删掉或计为成功，也不会在保存结果不确定时自动重放任务。

后续 AE 完整调用记录：`acceptance_results6.json` 在 `A0_CommitType` 停止，用时约 190 秒，尚未保存；截图中树形展开图标被大 ROI OCR 合并为 `□Step01`。已改成从 Action 类型锚点定位 Step 文字内部。`acceptance_results7.json` 通过该节点并保存 Step01/SQL 结构，但在 `A0_EditorReady` 停止，用时约 255 秒，返回 `partial, may_exist:true, workspace_ready:false`。dbx 确认仅有 Step01 的 SQL Action，SQLTEXT 为空。当前在本次创建的对象上校准代码编辑入口，尚未创建 Step02，也未执行任何 AE。REC3 尚未运行。

用户要求固定控件优先采用 0.85 截图模板后，三个创建 JSON 的查重标题、类型标签及类型值、Name 标签、打开与取消按钮已迁移。原整段零结果模板在更强的 10/100 合成反例上误判，已改为计数首位数字模板 `[696,719,7,11]`，外加对话框图片的 And 检查。8 张真实计数帧和 2 张合成帧中，数字 OCR 与 0.85 数字模板均符合预期；选择模板。实际 JSON 的 50 项离线检查、参数/服务/MCP 12 项回归及 schema 通过。真实查重探针在 Ctrl+O 后未打开对话框，未进入新识别节点，所以不能宣称迁移后的在线路径已通过。细节见 [截图识别方法对比](recognition_comparison.md)。

只读验收查询见 [acceptance_queries.sql](acceptance_queries.sql)，包括字段元数据、Record 属性、物理列及索引、行数、AE Step/SQL/PeopleCode 源码和编译结果。仍在创建中的对象可能尚未返回行；应以对应 MCP 调用结束后的 dbx 查询作为验收依据。
