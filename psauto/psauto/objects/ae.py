"""Only AE code/type/count bindings; all UI behavior is in create_ae.json."""

import re

from .common import bind_pipeline, identifier


def build(request):
    count = len(request.steps)
    values = {'name': request.name, 'name_regex': identifier(request.name),
              'property_identity_regex': r'(?:^|-\s*)' + identifier(request.name) + r'(?=\s*(?:\(|（))'}
    patches = {f'A{count - 1}_ParentReady': {'next': ['PSIDE_CreateAE_Saved']}}
    if request.state_record is not None or request.disable_restart is not None:
        patches['A0_StructureSave_named'] = {'next': ['AEProp_OpenFileMenu']}
        patches['AEProp_Ready'] = {'next': ['AEProp_StateTab' if request.state_record else 'AEProp_AdvancedTab']}
        if request.state_record:
            values['state_record'] = request.state_record
            values['state_record_regex'] = r'^\s*' + identifier(request.state_record) + r'\s*$'
            patches['AEProp_StateBound'] = {'next': ['AEProp_AdvancedTab' if request.disable_restart is not None else 'AEProp_OK']}
        if request.disable_restart is not None:
            selected = ['PSIDE/checkbox_selected.png', 'PSIDE/checkbox_selected_hover.png']
            unselected = ['PSIDE/checkbox_unchecked.png', 'PSIDE/checkbox_unchecked_hover.png']
            values['restart_wanted'] = selected if request.disable_restart else unselected
            values['restart_opposite'] = unselected if request.disable_restart else selected
    for index, step in enumerate(request.steps):
        values[f'code_{index}'] = step.code
        values[f'step_{index}_type'] = step.type
        values[f'step_{index}_type_regex'] = r'^\s*' + re.escape(step.type) + r'\s*$'
        values[f'editor_identity_{index}_regex'] = (
            r'^(?=.*(?:^|[^A-Z0-9_])' + identifier(request.name) + r'(?=[^A-Z0-9_]|$))'
            + r'(?=.*(?:^|[^A-Za-z0-9_])Step' + f'{index + 1:02d}'
            + r'(?=[^A-Za-z0-9_]|$)).*$')
        values[f'step_{index}_view_template'] = 'PSIDE/view_' + ('sql' if step.type == 'SQL' else 'peoplecode') + '_menu.png'
        values[f'step_{index}_editor_template'] = 'PSIDE/' + ('sql' if step.type == 'SQL' else 'peoplecode') + '_editor_icon.png'
        patches[f'A{index}_EditorReady'] = {'next': [f'A{index}_Focus' + ('SQL' if step.type == 'SQL' else 'PeopleCode') + 'Code']}
        if step.type == 'SQL':
            patches[f'A{index}_TypeFocus'] = {'next': [f'A{index}_CommitType']}
            patches[f'A{index}_PSIDE_CodeEditorSaved'] = {'next': [f'A{index}_CloseEditor']}
    return bind_pipeline('ae', 'PSIDE_CreateAE', values, patches)
