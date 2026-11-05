"""Only Record parameter/count bindings; all steps are in create_record.json."""

import re

from .common import bind_pipeline, identifier
from .models import RecordField


def build(request):
    count = len(request.fields)
    values = {'name': request.name, 'name_regex': identifier(request.name),
              'record_identity_regex': (r'(?:^|-\s*)' + identifier(request.name)
                                        + r'\s*[（(]\s*(?:记录|Record)'),
              'space_regex': '^' + re.escape(request.tablespace) + r'(?:\.|\s)'}
    view_build = request.type == 'SQL View'
    values['build_tables_template'] = 'PSIDE/checkbox_unchecked.png' if view_build else 'PSIDE/checkbox_selected.png'
    values['build_indexes_template'] = ('PSIDE/checkbox_unchecked.png' if view_build else
                                      ['PSIDE/checkbox_selected.png', 'PSIDE/checkbox_disabled_selected.png',
                                       'PSIDE/checkbox_disabled_selected_idle.png'])
    values['build_views_template'] = 'PSIDE/checkbox_selected.png' if view_build else 'PSIDE/checkbox_unchecked.png'
    for index, item in enumerate(request.fields):
        name = item if isinstance(item, str) else item.name
        values[f'field_{index}'] = name
        values[f'field_{index}_regex'] = identifier(name)
        values[f'field_{index}_row_regex'] = r'^\s*' + identifier(name) + r'\s*$'
    options = [(index, item) for index, item in enumerate(request.fields) if isinstance(item, RecordField)]
    patches = {f'R_Field{count - 1}_Inserted': {'next': [f'R_Attr{options[0][0]}_Bind' if options else 'R_TypeTab']}}
    patches['R_SpaceInitial'] = {'key': ord(request.tablespace[0])}
    if request.type == 'Derived/Work':
        patches['R_RecordTypeGroup'] = {'next': ['R_WorkTypeChoice']}
    elif request.type in {'SQL View', 'Dynamic View', 'Temporary Table'}:
        choice = {'SQL View': 'R_ViewTypeChoice', 'Dynamic View': 'R_DynamicTypeChoice',
                  'Temporary Table': 'R_TemporaryTypeChoice'}[request.type]
        patches['R_RecordTypeGroup'] = {'next': [choice]}
    if request.view_sql is not None:
        values['view_sql'] = request.view_sql
        values['view_editor_identity_regex'] = (r'(?:^|-\s*)' + identifier(request.name)
                                                + r'\s*\.\s*2\s*[（(]\s*SQL')
        patches['R_Save_ok'] = {'next': ['R_ViewNamed']}
    for position, (index, item) in enumerate(options):
        values[f'attr_{index}_next'] = f'R_Attr{options[position + 1][0]}_Bind' if position + 1 < len(options) else 'R_TypeTab'
        for attribute, label in [('key', 'Key'), ('alternate_search_key', 'Alternate'),
                                 ('listbox', 'List'), ('search_key', 'Search')]:
            values[f'attr_{index}_{attribute}'] = ([f'R_Attr{label}Checked', f'R_Attr{label}Check'] if getattr(item, attribute)
                                                 else [f'R_Attr{label}Unchecked', f'R_Attr{label}Uncheck'])
    if request.build:
        patches['PSIDE_CreateRecord_Saved'] = {'next': ['R_BuildMenu']}
        if view_build:
            patches['R_BuildSettingsOK'] = {'next': ['R_BuildTablesUnchecked', 'R_BuildTablesUncheck']}
            for node in ['R_BuildTablesChecked', 'R_BuildTablesCheck', 'R_BuildTablesUnchecked', 'R_BuildTablesUncheck']:
                patches[node] = {'next': ['R_BuildIndexesUnchecked', 'R_BuildIndexesUncheck']}
            for node in ['R_BuildIndexesChecked', 'R_BuildIndexesCheck', 'R_BuildIndexesUnchecked', 'R_BuildIndexesUncheck']:
                patches[node] = {'next': ['R_BuildViewsChecked', 'R_BuildViewsCheck']}
    return bind_pipeline('record', 'PSIDE_CreateRecord', values, patches)
