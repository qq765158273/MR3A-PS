These are small crops of real PSIDE captures, containing static controls and counters only.
They contain no login state, URLs or code. The lookup/save/build name crops
below contain the GM test object's name for the OCR regressions.

- `count_0.png`: `out/objects/20261104_111909_622202/after.png`, crop `(690,714,870,738)`.
- Other counters: the same crop from `out/objects/20261104_133313_970428/`:
  `035_R_Field0_AutoInserted.png` (1), `047_R_Field1_Cancel.png` (50),
  `058_R_Field2_Cancel.png` (17), `069_R_Field3_Cancel.png` (45),
  `080_R_Field4_Cancel.png` (7), `034_R_Field0_Insert.png` (blank).
- `lookup_title.png`: the static title template, originally cropped from the real Field lookup dialog.
- `steps_01_02.png`: `out/runs/20261104_144330_829162/000_A1_SelectStep.png`, crop `(560,240,670,400)`.
- `step_01_only.png`: `out/objects/20261104_135726_952891/after.png`, crop `(540,210,655,285)`.

Tests place these crops on blank canvases to exercise the actual native Maa recognition rules.
The 10/100 counters and the image with only Step02 are explicitly synthetic cases.
These compositions are regression inputs, not independent screenshots of a complete UI flow.

`checkbox_pair_00.png` through `checkbox_pair_11.png` contain just the 13×13
checkbox before and after 12 actual clicks in the successful REC3 run
`out/objects/20261104_164647_935317/`. `checkbox_pairs.json` records the source
frame names and boxes. Each 26×13 fixture places before on the left and after
on the right. Tests replay a changed frame and an unchanged frame, verifying
that an acknowledged click without a visual state change cannot continue.
Three additional inverse branches reuse the captured Key-uncheck pixels as
composed cases; they do not represent additional live interactions.

`lookup_name_caret.png` and `lookup_name_blurred.png` are crop
`(760,420,930,460)` from `out/objects/20261104_203219_476963/after.png` and
`out/runs/20261104_203429_948540/001_PSIDE_CreateRecord_query_name_check.png`.
The name is GM_MCP_REC6 in both. OCR reads the focused field's final character
as E; moving focus with Tab makes exact REC6 recognition pass. The test keeps
the exact name rule and does not normalize E to 6.

`save_name_caret.png` and `save_name_blurred.png`: crop `(840,520,1005,556)`
from `out/objects/20261104_203522_630973/after.png` and
`out/runs/20261104_204425_646013/001_R_Save_name.png`.
`build_scope_name.png`: crop `(780,415,960,505)` from
`out/runs/20261104_205014_802033/000_R_BuildDialog.png`.
The build-scope regression rejects the old tall ROI's E/6 misread and verifies
that the same real pixels pass the exact name rule in the 165×25 single line.

`ae_editor_title_step01.png` through `ae_editor_title_step04.png` are the first
`(0,0,1100,24)` pixels from the corresponding `A0_EditorReady` through
`A3_EditorReady` frames in `out/objects/20261105_075306_570062/`.
They contain the test AE name and Step, and no code body. Tests check the merged
identity OCR against the right object and Step, a wrong Step, a wrong object,
and a prefix-only object name that must not match the longer name.
额外对象名前缀反例使用测试内生成的标题，并同时验证完整名称能命中、短名称不能命中；正则判决仍调用 Maa 原生 OCR，不使用 Python 正则替代。

Step 标识符反例同样在测试内生成，覆盖 Step01A、XStep01、Step01_、额外数字和小写字母前后缀。测试拼入原有 SQL 图标、待保存和活动窗口图片，调用真实 Dirty 节点；只有完整 Step01 能发送一次 Ctrl+S，其余不发送保存键。
