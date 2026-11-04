These are small crops of real PSIDE captures, containing static controls and counters only.
They contain no login state, URLs, object names, or code.

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
