from typing import Callable

from ._key_extractor import default_dict_key_extractor
from ._basic import list_to_dict


def merge(
    data_a,
    data_b,
    key_extractors: list[Callable] = [default_dict_key_extractor]
):
    type_a = type(data_a)
    type_b = type(data_b)

    if type_a != type_b:
        raise TypeError('Types a incompatible to merge')

    rtn = None

    if type_a == dict:
        rtn = {}
        for key, value in data_a.items():
            type_a = type(value)
            if type_a in [dict, list]:
                rtn[key] = merge(data_a[key], data_b[key])
            else:
                rtn[key] = value
        for key, value in data_b.items():
            if key not in data_a:
                rtn[key] = value
        return rtn
    elif type_a == list:
        rtn_a, primitives_a, rest_a = list_to_dict(data_a, key_extractors)
        rtn_b, primitives_b, rest_b = list_to_dict(data_b, key_extractors)
        merged_rtn = merge(rtn_a, rtn_b, key_extractors)
        merged_rest = merge(rest_a, rest_b, key_extractors)    
        merged_primitives = primitives_b + [
            primitive 
            for primitive in primitives_a 
            if primitive not in primitives_b
        ]
        return (
            list(merged_rtn.values())
            + list(merged_rest.values())
            + merged_primitives
        )
