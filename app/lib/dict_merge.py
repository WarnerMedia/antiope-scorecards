import copy


def dict_merge(target, source):
    result = copy.deepcopy(target)

    for key, value in source.items():
        if key in result and isinstance(result[key], dict):
            result[key] = dict_merge(result[key], value)
        else:
            result[key] = value

    return result
