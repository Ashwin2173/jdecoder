from json import dumps
from collections import OrderedDict

CONSTANT_Class = 7
CONSTANT_Fieldref = 9
CONSTANT_Methodref = 10
CONSTANT_InterfaceMethodref = 11
CONSTANT_String = 8
CONSTANT_Integer = 3
CONSTANT_Float = 4
CONSTANT_Long = 5
CONSTANT_Double = 6
CONSTANT_NameAndType = 12
CONSTANT_Utf8 = 1
CONSTANT_MethodHandle = 15
CONSTANT_MethodType = 16
CONSTANT_InvokeDynamic = 18

def read_u1(f): return f.read(1)
def read_u2(f): return f.read(2)
def read_u4(f): return f.read(4)
def read_un(f, n): return f.read(n)
def to_int(v): return int.from_bytes(v, byteorder="big")
def to_str(v): return v.decode("utf-8")

def parse_constant_pool(f):
    const = list()
    cp_count = to_int(read_u2(f))
    for _ in range(cp_count - 1):
        tag = to_int(read_u1(f))
        if tag == CONSTANT_Methodref:
            const.append({
                "type": "CONSTANT_Methodref",
                "class_index": to_int(read_u2(f)),
                "name_and_type_index": to_int(read_u2(f))
            })
        elif tag == CONSTANT_Class:
            const.append({
                "type": "CONSTANT_Class",
                "name_index": to_int(read_u2(f))
            })
        elif tag == CONSTANT_NameAndType:
            const.append({
                "type": "CONSTANT_NameAndType",
                "name_index": to_int(read_u2(f)),
                "descriptor_index": to_int(read_u2(f))
            })
        elif tag == CONSTANT_Utf8:
            length = to_int(read_u2(f))
            const.append({
                "type": "CONSTANT_Utf8",
                "length": length,
                "bytes": to_str(read_un(f, length))
            })
        elif tag == CONSTANT_String:
            const.append({
                "type": "CONSTANT_String",
                "string_index": to_int(read_u2(f))
            })
        else:
            print("Unhanled const type:", tag)
            exit(1)
    return const

def parse_code_attribute(f, program):
    return {
        "max_stack": to_int(read_u2(f)),
        "max_locals": to_int(read_u2(f)),
        "code_length": (code_length := to_int(read_u4(f))),
        "code": str(read_un(f, code_length)),
        "exception_table_length": (exp_length := to_int(read_u2(f))),
        "exception_table": [{
            "start_pc": to_int(read_u2(f)),
            "end_pc": to_int(read_u2(f)),
            "handler_pc": to_int(read_u2(f)),
            "catch_type": to_int(read_u2(f))
        } for _ in range(exp_length)],
        "attributes_count": (attr_count := to_int(read_u2(f))),
        "attributes": parse_attribute_info(f, program, attr_count)
    }

def parse_attribute_info(f, program, count):
    pool = program['constant_pool']
    attr_list = list()
    for _ in range(count):
        info = {
            "attribute_name_index": (index := to_int(read_u2(f))), 
            "attribute_length": (length := to_int(read_u4(f))),
            "info": None
        }
        tag = pool[index-1]['bytes']
        if tag == 'SourceFile':
            info['info'] = {
                "type": "SourceFile",
                "sourcefile_index": to_int(read_u2(f))
            }
        elif tag == 'Code':
            info['info'] = {
                "type": "Code",
                "info": parse_code_attribute(f, program)
            }
        elif tag == 'LineNumberTable':
            info['info'] = {
                "type": "LineNumberTable",
                "info": {
                    "line_number_table_length": (length := to_int(read_u2(f))),
                    "line_number_table": [{
                        "start_pc": to_int(read_u2(f)),
                        "line_number": to_int(read_u2(f))
                    } for _ in range(length)]
                }
            }
        else:
            print("unhandled attribute:", tag)
            exit(1)
        attr_list.append(info)
    return attr_list

def parse_method(f, program, count):
    methods = list()
    for _ in range(count):
        methods.append({
            "access_flags": to_str(read_u2(f)),
            "name_index": to_int(read_u2(f)),
            "descriptor_index": to_int(read_u2(f)),
            "attributes_count": (count := to_int(read_u2(f))),
            "attributes": parse_attribute_info(f, program, count)
        })
    return methods

def parse() -> None:
    file_path = "Main.class"
    program = OrderedDict()
    with open(file_path, 'rb') as f:
        program['magic'] = str(read_u4(f))
        program['major'] = to_int(read_u2(f))
        program['minor'] = to_int(read_u2(f))
        program['constant_pool'] = parse_constant_pool(f)
        program['access_flags'] = to_int(read_u2(f))
        program['this_class'] = to_int(read_u2(f))
        program['super_class'] = to_int(read_u2(f))
        program['interfaces_count'] = to_int(read_u2(f))
        program['interfaces'] = list()
        program['fields_count'] = to_int(read_u2(f))
        program['fields'] = list()
        program['methods_count'] = to_int(read_u2(f))
        program['methods'] = parse_method(f, program, program['methods_count'])
        program['attributes_count'] = to_int(read_u2(f))
        program['attributes'] = parse_attribute_info(f, program, program['attributes_count'])
    return program
    
if __name__ == "__main__":
    print(dumps(parse(), indent=2))