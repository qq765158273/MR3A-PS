"""Bind an existing-definition manifest to the native Project pipeline."""

from .common import bind_pipeline, identifier


TYPE_KEYS = {
    'AE': [36, 40, 40, 40, 40, 13],
    'Record': [36, 82, 13],
    'Field': [36, 70, 40, 40, 40, 40, 13],
}


def build(request):
    values = {
        'name': request.name,
        'name_regex': r'^\s*' + identifier(request.name) + r'\s*$',
        'project_title_regex': r'HRDEV\s*-\s*' + identifier(request.name) + r'\s*$',
    }
    patches = {f'P{len(request.definitions) - 1}_Inserted': {'next': ['P_CloseDialog']}}
    for index, item in enumerate(request.definitions):
        kind = item.type.lower()
        values[f'definition_{index}'] = item.name
        values[f'definition_{index}_regex'] = r'^\s*' + identifier(item.name) + r'\s*$'
        values[f'type_{index}_template'] = f'PSIDE/project_type_{kind}.png'
        values[f'related_{index}_end_template'] = f'PSIDE/project_related_{kind}_selected.png'
        values[f'related_{index}_template'] = (f'PSIDE/project_related_{kind}_top_selected.png'
                                               if item.type == 'Record' else values[f'related_{index}_end_template'])
        if item.type == 'Record':
            patches[f'P{index}_Select'] = {'next': [f'P{index}_RelatedScrollTop']}
        patches[f'P{index}_TypeSelect'] = {'key': TYPE_KEYS[item.type]}
    return bind_pipeline('project', 'PSIDE_CreateProject', values, patches)
