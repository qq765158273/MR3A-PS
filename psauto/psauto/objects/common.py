"""Bind data to native JSON resources; no UI steps or recognition logic live here."""

import copy
import json
from pathlib import Path
import re


RESOURCE = Path(__file__).resolve().parents[3] / 'assets/resource/pipeline/PSIDE'


def identifier(value):
    return re.escape(value).replace('_', '[_ ]+')


def bind_pipeline(kind, entry, values, patches=None):
    original = json.loads((RESOURCE / f'create_{kind}.json').read_text(encoding='utf-8'))
    template = copy.deepcopy(original)
    template[entry]['enabled'] = True
    for name, properties in (patches or {}).items():
        template[name].update(properties)
    missing = {}

    def bind(value, node_name):
        if isinstance(value, str) and value.startswith('__PARAM_') and value.endswith('__'):
            key = value[len('__PARAM_'):-2]
            if key not in values:
                missing.setdefault(node_name, set()).add(key)
                return value
            return values[key]  # Payload data is returned once, never evaluated or substituted again.
        if isinstance(value, list):
            return [bind(item, node_name) for item in value]
        if isinstance(value, dict):
            return {key: bind(item, node_name) for key, item in value.items()}
        return value

    bound = {name: bind(properties, name) for name, properties in template.items()}
    visited, pending = set(), [entry]
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        if missing.get(name):
            raise ValueError(f'Missing pipeline parameters for {name}: {sorted(missing[name])}')
        pending.extend(bound[name].get('next', []))
    override = {}
    for name, properties in bound.items():
        changed = {key: value for key, value in properties.items() if value != original[name].get(key)}
        if changed:
            override[name] = changed
    return entry, override
