import os, re
import jinja2
from collections import OrderedDict
import typer
from h2ctypes.common import _CXX2CTYPES

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
)

def get_struct_str(filepath):
    with open(filepath, 'r') as f:
        context = f.read()
    type_defs_pattern = r"typedef\s+(\w+)\s+(\w+)\s*;*"
    type_defs_results = re.findall(type_defs_pattern, context, re.DOTALL)
    type_defs = {}
    for (kind, name) in type_defs_results:
        if kind != 'struct':
            type_defs[name] = kind
    pattern = r"(struct|enum)\s+\w+\s*\{.*\}.*;"
    matched = re.search(pattern, context, re.DOTALL)
    if matched:
        context = matched.group()
        context = re.sub(r'/\*.*?\*/', '', context, flags=re.DOTALL)
        context = re.sub(r'//.*$', '', context, flags=re.MULTILINE)
    else:
        context = ''
    return context, type_defs

def parse_str2json(context):
    structs = {}
    enums = {}
    parsing = None
    parsing_type = None
    parse_end_counter = 1
    name_pattern = re.compile(r'(struct|enum)\s+(\w+)\s*\{*')
    kv_pattern = re.compile(r'(\w+)\s+(\w+)\s*;*')
    for line in context.split('\n'):
        cline = line.strip()
        if not cline:
            continue
        if 'struct ' in cline or 'enum ' in cline:
            assert not parsing, f'parsing failed! {cline}'
            parse_end_counter = 1
            name = name_pattern.search(cline).group(2)
            parsing = name
            if 'struct ' in cline:
                parsing_type = 'struct'
                structs[parsing] = OrderedDict()
            else:
                parsing_type = 'enum'
                enums[parsing] = OrderedDict()
            #print(f'start parsing struct|enum: {name}...')
        else:
            cline = cline.strip('{ ')
            if 'union' in cline:
                cline = cline.replace('union', '').strip()
                parse_end_counter += 1
            if not cline:
                continue
            if '}' in cline:
                assert 'struct' not in cline and 'enum' not in cline, cline
                parse_end_counter -= 1
                cline = ''
            if parse_end_counter == 0:
                parsing = None
                parsing_type = None
            if not cline:
                continue
            if parsing_type == 'struct':
                kv_match = kv_pattern.search(cline)
                k = kv_match.group(1)
                v = kv_match.group(2)
                structs[parsing][v] = k
            else:
                enums[parsing][1] = cline
            assert 'struct ' not in cline and 'enum ' not in cline, cline
    return structs, enums

def load_structs(filepaths):
    result_structs = {}
    result_enums = {}
    result_type_defs = {}
    for filepath in filepaths:
        struct_context, type_defs = get_struct_str(filepath)
        structs, enums = parse_str2json(struct_context)
        result_structs.update(structs)
        result_enums.update(enums)
        result_type_defs.update(type_defs)
    #print('[parsing] done')
    return result_structs, result_enums, result_type_defs

def parse2dict(item, base_infos, ret=OrderedDict()):
    structs, enums, type_defs = base_infos
    for k, v in item.items():
        if v in enums:
            ret[k] = 'uint32_t'
        elif v in structs:
            ext_ret = parse2dict(structs[v], base_infos)
            ret.update(ext_ret)
        elif v in type_defs:
            ret[k] = type_defs[v]
        else:
            ret[k]= v
    return ret

@app.command()
def dump(dump_structname: str,
        input_header_files: list[str],
        dump_json_path: str = '{dump_structname}.json',
        dump_py_path: str = '{dump_structname}.py',
        noconvert: bool = False,
        pack: int = 8,
    ):
    import json
    base_infos = load_structs(input_header_files)
    structs, enums, type_defs = base_infos
    return_dict = parse2dict(structs[dump_structname], base_infos)
    if noconvert:
        dump_json_path = dump_json_path.format(**locals())
        with open(dump_json_path, 'w') as f:
            json.dump(return_dict, f, indent=2)
        print(f'[dump] {dump_json_path}')
    else:
        # process ctypes map
        template_path = os.path.join(os.path.dirname(__file__), 'struct.py.j2')
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.dirname(template_path)),
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
        )
        template = env.get_template(os.path.basename(template_path))
        res = template.render({
            'struct_name': dump_structname,
            'pack': pack,
            'field_infos': [{'name': k, 'ctypes': _CXX2CTYPES[v]} for k, v in return_dict.items()],
        })
        dump_py_path = dump_py_path.format(**locals())
        with open(dump_py_path, 'w') as f:
            f.write(res)
        print(f'[dump] {dump_py_path}')

if __name__ == '__main__':
    app()
