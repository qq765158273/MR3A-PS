"""Only Field argument bindings; operations are in create_field.json."""

from .common import bind_pipeline, identifier


def build(request):
    values = {'name': request.name, 'name_regex': identifier(request.name),
              'field_type_regex': '^' + request.type + '$',
              'length_text': str(request.length),
              'label_id': request.label_id,
              'long_name': request.long_name, 'short_name': request.short_name}
    patches = {'F_TypeCheck': {'next': ['F_LengthFocus' if request.type == 'Character' else 'F_LabelIDFocus']}}
    if request.type == 'Date':
        patches['F_TypeSelect'] = {'next': ['F_DateSelect']}
    return bind_pipeline('field', 'PSIDE_CreateField', values, patches)
