# 常用类型验收证据

五次从头MCP均保存关闭且释放工作台：SQL View＋Build、Dynamic View、Temporary Table＋Build、一表AE、两表AE。SQL Table和Work是原有能力，本轮增加其余三种及AE绑定。

- [三种Record同一服务连续结果](record_mcp_results.json)
- [一表AE](ae_one_mcp_result.json) / [两表AE](ae_two_mcp_result.json)
- [DBX类型、SQL、物理对象及AE属性](dbx.json)
- [SQL View节点](view_nodes.csv) / [Dynamic View节点](dynamic_nodes.csv) / [Temporary Table节点](temporary_nodes.csv)
- [一表AE节点](ae_one_nodes.csv) / [两表AE节点](ae_two_nodes.csv)
- [SQL编辑器保存](view_R_ViewSQLSaved.png) / [Build选项](view_R_BuildExecute.png)
- [AE临时表绑定](ae_one_AEProp_Temp0_Bound.png) / [两表绑定末行](ae_two_AEProp_Temp1_Bound.png)
- [Restart已确认](ae_one_AEProp_RestartVerified.png) / [已知Project提示](ae_one_AEProp_TempProjectPrompt.png)
- [普通140项64通过76跳过](unit_tests.txt)
- [新增视觉5项](new_vision_tests.txt)、[临时表模块3项](temp_tests.txt)、[原AE属性6项](ae_property_regression.txt)、[旧视觉14项](existing_vision_regression.txt)

每个样本的请求、summary、timings均按view/dynamic/temporary/ae_one/ae_two前缀保存。节点CSV来自Maa原生报告。新增参数测试与普通套件重叠，不累计整体通过数；未执行AE，也没有完成部门Excel导出。

参数与范围见 [功能说明](../../common_types.md)，业务代码独立审核见 [pshelp报告](../../pshelp_department_code_objects_review.md)。原始其他AE源码/业务行只保存在本机忽略目录，未放入这份功能证据。
