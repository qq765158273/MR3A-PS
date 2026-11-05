# PSIDE Project 保存能力

`save_project(name, definitions)` 将已经保存的 AE、Record、Field 和其原生 Related Definitions 归集到新 HRDEV 数据库 Project，保存后返回空白 Untitled 工作台。业务步骤、识别、有限等待及停止都在 `assets/resource/pipeline/PSIDE/create_project.json`；Python 只校验参数、绑定、调度及读取原生终态。

## 参数

```json
{
  "name": "GM_DEPT_EXPORT",
  "definitions": [
    {"type": "AE", "name": "GM_DEPT_XL4"},
    {"type": "Record", "name": "GM_DEPT_AET"}
  ]
}
```

该示例工程已创建，复测应换名。工程名以 GM 开头，当前支持 3–15 个大写字母、数字或下划线；15 是 Save Project As 输入框可完整视觉确认的实现边界，不是 PeopleSoft 本身的名称上限。清单支持 1–20 项，类型 AE/Record/Field 的名称分别不超过 12/15/18 字符，拒绝通配符、重复的类型/名称组合及其他类型。更新服务后须重新连接 MCP 才能看到新工具。

每项均选择其原生全部 Related Definitions。AE 会带入 Section、PeopleCode、SQL 等；本次显式加入 AET，进一步带入其字段/标签。关联范围取决于 PSIDE，不解析代码中的动态字符串来猜测依赖；第三方 Java/JAR 也不属于 Project 定义。已存在工程返回 already_exists，不支持追加或覆盖。Project 归集数据库定义，不冻结代码版本或生成迁移文件。

## 原生判决

| 阶段 | 继续条件 |
| --- | --- |
| 入口 | HRDEV/Untitled 完整标题、空闲工具栏、成员区全白、中央编辑区空白；其他工程、未保存成员或模态窗口停止 |
| 工程查重 | 原生 Open Definition，Project 类型、完整输入名；存在时识别完整标题，打开后不写入，新建空 Project 释放；多个结果/未知提示停止 |
| 每项搜索 | New Search 清空旧结果、模板确认类型、局部完整名称 OCR；结果区仍空才点击一次搜索 |
| 每项插入 | 数字小 ROI 必须为 1、首行完整名称、类型、全部关联类别选中模板及行选中蓝色同时满足；Insert 只点击一次 |
| 插入反馈 | 原生 definition(s) inserted.；允许 0，因为上一个对象的关联可能已加入本项，不因此重放 |
| 工程保存 | File/Save Project、Save Project As、完整输入名；保存后必须识别 HRDEV - 完整工程名 的终止标题 |
| 释放 | Ctrl+N，明确选中 Project，回到无成员、无编辑器的 Untitled，再发出 SavedAndClosed |

每项 Inserted、工程 Saved、SavedAndClosed 均为本任务必需原生完成事件，缺失不能返回成功。保存前后未知提示停止，不自动确认覆盖；业务中途失败不重放。继承串行、超时不确定保护、证据失败隔离和阻止后续操作的约束。

新节点默认有限等待 5 秒，输入后固定等待 80–150ms；静态模板通常 0.85，选中类别模板 0.97；动态名严格局部 OCR，结果数独立数字 OCR。选中蓝色按实际画布允许小范围色差，灰白状态不能通过。没有对工程树同名小字重复 OCR，避免低质量冗余判决。 Record 的关联列表会滚动。P2 补强后，在结果行选中之后先验证末端选中模板，再用两个原生 Click 点击滚动条上箭头，保持选择并显示首部；Insert 还必须通过首部选中模板。两视口重叠覆盖当前版本的类别。顶部未选或滚动没有生效即停止，不以末端蓝色代替完整选择。

## 实测与证据

正式 GM_DEPT_EXPORT 通过新 stdio MCP 从空白完整创建：55 节点、原生跨度 37.250 秒、0 节点/动作失败，2 次额外扫描、3 次候选未命中；证据导出另约 9.862 秒，不重复相加。返回 saved_and_closed、definitions_added=2、evidence complete、next_operation_allowed=true。DBX 只读确认 10 个成员：AE 程序33、MAIN Section34、Step01/OnExecute PeopleCode43、AET及两条Record Field成员0、两个字段及标签2；编译长度7264。

同一新 MCP 实例又先执行重名请求，返回 already_exists、saved=false、workspace_ready/next_operation_allowed=true；随后继续创建三类型测试工程 GM_PS_PROJ_T，返回 saved_and_closed、definitions_added=3。该次工具70.216秒，其中原生68节点/54.844秒、证据导出13.754秒，0节点/动作失败；与两对象样本的操作量不同，不直接当作同工作量性能对照。重名返回的 success=false 属于预期拒绝，客户端测试另记 expected_outcome_passed=true，不把它计为保存成功。DBX 复查确认重名调用前后 GM_DEPT_EXPORT 时间戳与10个成员完全一致，三类型测试工程有12个成员，包含额外字段及标签。校准工程 GM_DEPT_P_CAL 属于分段探索，不计完整 MCP 通过。

最终普通套件128项中58通过、70显式跳过。Project模块6项通过，其中2项参数与普通套件重叠，4项为原生离线视觉测试；覆盖三个类型正确选中，以及前缀名、相关类别/行未选、空/2/11计数、错误保存标题和非空/模态工作台。离线点击/按键仅记录内存。不同批次不累加成整体通过率。

截图、CSV、分项日志和DBX见 [验收证据](images/acceptance-project-20261105/README.md)。pshelp 初审、P2补核和修复定向复验按版本保留。主控已全文读取修复附记并核对32个最终源码/图像SHA；定向独立native一项及Home失效模型均验证新guard拒绝缺首部状态，P2在指定布局下关闭。见 [独立审核报告](pshelp_project_review.md)。

## Excel 执行边界

PSIDE 本身可通过 Edit/Run Program 在它所在的远程 Windows 上执行 AE并写文件，调度器是另一条可选路径。早先样本实际到达PeopleCode，随后JVM启动失败/RC8。只读检查进一步确认pside.exe的PE machine为8664（64位）；PeopleTools客户端根内未找到配套JVM，Oracle目录发现的旧JVM文件版本为5.0.170.4及5.0.110.3，未拿来加载或替换。

后续应补齐与PeopleTools8.57.11匹配的64位Java及HPS/POI报表依赖，再实测本地Run。Project保存不代表Excel已经生成；业务草稿仍未完成导出验收，见 [部门demo](department_export_demo.md)。

## Record 关联类别 P2 补强与最终回归

pshelp 在补核中确认：Home 未生效但按键回执成功时，原末端模板不能区分隐藏首部未选。它是特定输入故障模型下的保护缺口，不表示已有工程实际缺成员。修复增加 Record 的末端检查、两次滚动条点击和首部模板；AE/Field 保持原路径。受控校准确认滚动条保持全选；Ctrl+Home 会清除多选，未用于生产。新顶部模板来自真实画面，测试fixture只把真实顶部列表像素贴到原名称/计数/行选中截图的[974,412,158,92]区域，明确为合成反例素材。

新增native用例从滚动前末端真实图开始，两次点击后分别呈现正确顶部或顶部两类未选，后者不得Insert，正确态只Insert一次。最终Project模块6/6通过；普通128项58通过、70跳过。原127项/5项日志保留为修复前历史，不与最终批次累计。

修复后新MCP回归 GMPRJFIX01：57/57节点、原生44.969秒、0节点/动作失败、2次扫描重试、3次候选未命中，保存关闭/证据complete/下一操作允许均通过；证据导出另12.596秒。DBX确认10个成员与GM_DEPT_EXPORT完全一致，原工程时间戳仍未改变。该次与初次创建的运行环境/耗时不同，不能把7.719秒差值全部归因于新增两次点击。

另一次临时回归名称GM_DEPT_EXP_R的搜索返回了相近名称GM_DEPT_EXPORT，完整身份保护没有接受它，停止在query_open，未保存、也未进入对象插入。搜索匹配规则未单独确认；这次失败作为已阻止的搜索边界保留，未计保存成功。人工取消本次查重窗口后，重新以独立名称GMPRJFIX01执行上述完整回归；运行时没有自动重放。
