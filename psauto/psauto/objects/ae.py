"""Only AE code/type/count bindings; all UI behavior is in create_ae.json."""

import re

from .common import bind_pipeline, identifier


def build(request):
    count = len(request.steps)
    values = {'name': request.name, 'name_regex': identifier(request.name)}
    patches = {f'A{count - 1}_ParentReady': {'next': ['PSIDE_CreateAE_Saved']}}
    for index, step in enumerate(request.steps):
        values[f'code_{index}'] = step.code
        values[f'step_{index}_type'] = step.type
        values[f'step_{index}_type_regex'] = r'^\s*' + re.escape(step.type) + r'\s*$'
        values[f'step_{index}_view_template'] = 'PSIDE/view_' + ('sql' if step.type == 'SQL' else 'peoplecode') + '_menu.png'
        values[f'step_{index}_editor_template'] = 'PSIDE/' + ('sql' if step.type == 'SQL' else 'peoplecode') + '_editor_icon.png'
        patches[f'A{index}_EditorReady'] = {'next': [f'A{index}_Focus' + ('SQL' if step.type == 'SQL' else 'PeopleCode') + 'Code']}
        if step.type == 'SQL':
            patches[f'A{index}_TypeFocus'] = {'next': [f'A{index}_CommitType']}
            patches[f'A{index}_PSIDE_CodeEditorSaved'] = {'next': [f'A{index}_CloseEditor']}
    return bind_pipeline('ae', 'PSIDE_CreateAE', values, patches)
