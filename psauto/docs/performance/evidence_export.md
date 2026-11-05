# 证据导出的内存与耗时

2026-11-05，相对 `722d2ac`，改用 Maa 公开接口逐节点导出证据。208 节点离线原生任务中，Python 导出进程的新增私有内存峰值从 2.43 GiB 降至 24.85 MiB；单次导出从 24.889 秒降至 22.380 秒。主要收益是降低内存，耗时仅小幅改善，不能据此声称整条业务流水线提速 10%。

## 实现与保留内容

`TaskDetail.nodes` 虽然延迟加载，但首次访问会读取并缓存全部 `NodeDetail`，其中包含识别原图和 draw 图。208 张 1920×1080 BGR 原图本身约 1.20 GiB，另有 draw 图及 SDK 临时复制；原有像素去重发生在整批加载之后。

改用公开 `TaskDetail.node_id_list` 和 `Tasker.get_node_detail`，每次读取一个节点，生成纯 metadata、写出无损图像后释放详情，再读取下一节点。不访问 SDK 私有成员，不修改安装中的 Maa。调用者提供 `EvidenceSink` 时从其 tasker 取得接口，也可显式传入 tasker；旧的无 tasker 调用保留兼容路径，并记录 `eager_compatibility`，不将其称为逐节点导出。缺失节点仍抛错，不静默漏证据。

SHA-256 直接读取连续 BGR 数组的 buffer，避免每张图先 `tobytes()`；非连续输入先转为相同 C 顺序。Pillow 使用公开的 BGR raw decoder 转换 RGB，避免反向切片引起的额外 Python 像素复制。PNG 仍为无损、`compress_level=1`，通过 BytesIO 将编码与磁盘写入分别计时，保留按像素与识别 ID 去重。

Maa 原生事件、逐节点计时、失败候选截图、节点/事件到图片的映射和业务判断全部保留。失败候选详情也在下一次读取前释放。前轮的保存/关闭/Build 业务事实、证据故障阻塞、幂等关闭及客户端清理语义保持；导出异常后仍能写入已完成的性能分项。

## 对照方法和结果

使用历史 Record `out/objects/20261105_140117_227126` 中的原始 PNG，作为离线控制器截图输入。运行相同 208 节点的原生 Maa `ColorMatch` / `DoNothing` 链；没有真实浏览器、数据库或输入动作。每个实现使用独立 Python 进程。三组各产生 208 节点、1664 事件、99 张去重 PNG。

Windows `GetProcessMemoryInfo` 每 20ms 采样，统计导出前到导出结束的 working set / private 峰值，以及相对导出前的增量。采样只覆盖当前 Python 导出进程，不包含 Maa 其他进程、Chrome 或整机内存；也不统计任务创建阶段。轮询可能漏掉短于采样间隔的峰值，结果是观测值。

| 实现 | 导出耗时 | 导出期 private 增量峰值 | 导出期 RSS 增量峰值 |
| --- | ---: | ---: | ---: |
| `722d2ac` 原实现 | 24.889 秒 | 2489.86 MiB | 2485.11 MiB |
| 原算法加分项计时 | 24.046 秒 | 2497.48 MiB | 2492.14 MiB |
| 本轮逐节点导出 | 22.380 秒 | 24.85 MiB | 24.84 MiB |

相对原实现，观测到新增 private 峰值下降 99.0%，导出耗时下降约 10.1%。每组仅一次完整测量；原算法加计时版本甚至比未加计时略快，说明耗时仍有运行波动。不能把此单次差值当作稳定的平均提速或长期成功率。64 节点先导测量另用于确认内存预算，未混入 208 节点结果。

新旧所有 PNG 逐像素 SHA-256 与文件字节完全一致；规范化后 report / events / summary 也完全一致，仅排除原生运行中自然变化的 `timing`、`elapsed_ms`、`pipeline_event_ms`、`phase_ms`。没有删掉失败、事件、动作、识别详情、截图引用或顺序来凑一致。

原始指标和每张图像 RGB 摘要：[原实现](export/export_original_208.json)、[加计时的原算法](export/export_baseline_208.json)、[逐节点实现](export/export_stream_208.json)、[内容比较](export/comparison.json)。本机完整证据分别位于 `out/export_original_208`、`out/export_baseline_208`、`out/export_stream_208`。加计时的原算法快照为本机 `out/evidence_profile_baseline.py`，它是诊断对照，不是新增运行入口；原实现可直接从 Git 基线提取重现。

## 分项日志与剩余开销

每次 MCP 任务继续写原有 `timings.json`，新增 `evidence_export` 对象，包含 `node_access`、`total_ms`、`phases_ms`、`unattributed_ms` 与计数。原有 `evidence_export_ms` 保留；它与新对象的 total 是同一阶段的两层测量，不能相加，也不能与 Maa 原生任务阶段重复累计。

| 分项 | 加计时的原算法 | 逐节点实现 |
| --- | ---: | ---: |
| 详情读取（SDK 内含 raw/draw 深拷贝） | 8.543 秒 | 10.025 秒 |
| 哈希前复制/准备 | 0.982 秒 | 0.001 秒 |
| SHA-256 | 4.617 秒 | 4.593 秒 |
| BGR → RGB | 2.814 秒 | 0.820 秒 |
| PNG 编码 | 6.218 秒 | 6.153 秒 |
| PNG 写盘 | 0.206 秒 | 0.128 秒 |
| metadata / 其他未归属 | 0.667 秒 | 0.660 秒 |

详情读取仍有 SDK 提供的原图及 draw 图复制，逐节点读取并没有消除这部分工作；交错读取/释放的实测时间反而更长。当前主要剩余成本是详情读取、无损编码及像素哈希，磁盘写入占比较小。不能将约 22 秒全部归咎于磁盘或 Playwright；这段发生在原生任务完成之后。

## 验证与复现

新增测试覆盖逐节点释放 raw/draw、禁止访问整批 `.nodes`、明确 tasker/trace 两种调用、旧接口兼容、缺失节点失败、连续/跨步/转置 BGR 的颜色与去重、候选图释放及写盘异常。真实 Maa 重试和失败动作测试继续核对完整原生节点计时。服务增加失败时性能分项写入且保存/关闭事实不变的测试。普通全套 109 项：52 通过、57 项按集成开关跳过；未将跳过项计为通过。本机日志为 `out/export_unit_tests.log`。

从仓库根目录运行下列命令，每条等待完成后再运行下一条；baseline 文件使用 UTF-8 保存 `git show 722d2ac:psauto/psauto/evidence.py` 的输出：

```powershell
.psauto-runtime/venv/Scripts/python.exe psauto/benchmarks/evidence_export.py --source psauto/out/objects/20261105_140117_227126 --output psauto/out/export_original_repeat --exporter psauto/out/evidence_original.py
.psauto-runtime/venv/Scripts/python.exe psauto/benchmarks/evidence_export.py --source psauto/out/objects/20261105_140117_227126 --output psauto/out/export_stream_repeat
```

需要本机保留完整原图证据，输出目录必须不存在。脚本只允许 `DoNothing`，内存采样超过 6 GiB 时退出本次 benchmark 进程；不接入业务浏览器。`benchmark.json` 保存进程内存、导出分项、实现文件 SHA 和图片摘要，`normalized.json` 用于比较非计时 metadata。

## 真实接入结果

主控以新启动的 MCP 实例完整创建五字段 `GM_EXP_REC`、Build、保存并关闭：208 节点全部完成，0 重试/节点失败/动作失败，证据 complete 且允许下一操作。DBX 确认字段顺序/属性、HRAPP 物理表、3 个 VALID 索引及 0 行。真实导出记录 `streaming`，包括 20 个失败候选详情，228 张 raw 去重为 100 PNG。

本次完整调用 230.34 秒、导出 27.565 秒，均高于此前现场样本，不将其计为真实业务提速。执行阶段已增加约 56 秒，截图和输入调用也明显变慢；该阶段发生在导出之前，不能由本轮导出优化解释。不同时间现场对照与离线同输入对照分开报告，详见 [完整截图、计时及 DBX](../images/acceptance-export-20261105/README.md)。
