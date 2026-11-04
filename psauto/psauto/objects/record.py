"""Only Record parameter/count bindings; all steps are in create_record.json."""

import re

from .common import bind_pipeline, identifier
from .models import RecordField


def build(request):
    count = len(request.fields)
    values = {'name': request.name, 'name_regex': identifier(request.name),
              'space_regex': '^' + re.escape(request.tablespace) + r'(?:\.|\s)'}
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
    for position, (index, item) in enumerate(options):
        values[f'attr_{index}_next'] = f'R_Attr{options[position + 1][0]}_Bind' if position + 1 < len(options) else 'R_TypeTab'
        for attribute, label in [('key', 'Key'), ('alternate_search_key', 'Alternate'),
                                 ('listbox', 'List'), ('search_key', 'Search')]:
            values[f'attr_{index}_{attribute}'] = ([f'R_Attr{label}Checked', f'R_Attr{label}Check'] if getattr(item, attribute)
                                                 else [f'R_Attr{label}Unchecked', f'R_Attr{label}Uncheck'])
    if request.build:
        patches['PSIDE_CreateRecord_Saved'] = {'next': ['R_BuildMenu']}
    return bind_pipeline('record', 'PSIDE_CreateRecord', values, patches)
