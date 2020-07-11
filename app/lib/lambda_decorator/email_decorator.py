import functools
from lib.dynamodb import user_table

from . import exceptions


def email_decorator(func):
    @functools.wraps(func)
    def wrapper_decorator(event, context):
        email = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('email')
        if email:
            event['userRecord'] = user_table.get_user(email) or {}
        else:
            raise exceptions.HttpInvalidException('bad request')
        return func(event, context)
    return wrapper_decorator
