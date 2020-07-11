import base64


def string_to_base64(value):
    return base64.b64encode(value.encode('utf-8')).decode('utf-8')


def base64_to_string(value):
    return base64.b64decode(value).decode('utf-8')
