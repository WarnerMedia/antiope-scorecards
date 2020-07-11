"""
Various decorators for common transformations/logic needed by lambda handlers
"""
import base64
from decimal import Decimal
import functools
import json

from lib.logger import logger, update_log_format
from lib.dict_merge import dict_merge
from . import exceptions


def serializer(obj):
    """Add json serialization support for Decimal and classes"""
    if isinstance(obj, Decimal):
        return int(obj)
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    return obj.__dict__


def parse_event(event):
    """Parses incoming API gateway event"""
    if event.get('isBase64Encoded'):
        event['body'] = base64.b64decode(event.get('body')).decode('utf-8')
    elif event.get('body'):
        try:
            if isinstance(event['body'], str):
                event['body'] = json.loads(event['body'])
        except:
            raise exceptions.HttpInvalidException('Unable to parse JSON body')
    return event


def format_result(result):
    """JSON dumps with custom serializer"""
    if isinstance(result, dict):
        return json.dumps(result, default=serializer)
    return result


def generate_default_response():
    """Default API gateway response"""
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': '*',
        },
        'body': 'OK'
    }


def api_decorator(func):
    """
    Decorator to wrap all API calls

    Converts HttpExceptions raised by handler to appropriate API gateway response
    Converts handler return to API gateway response as needed.

    If the handler returns a dictionary with a "statusCode" attribute the returned value
    is treated as an API gateway response dictionary. Otherwise the returned value is
    used as the body for an apigateway response.
    """

    @functools.wraps(func)
    def wrapper_decorator(event, context):
        response = generate_default_response()

        try:
            event = parse_event(event)
            logger.info('Event: %s', json.dumps(event, default=str))
            result = func(event, context)
            # if recieved raw lambda response, merge with default response
            if isinstance(result, dict) and 'statusCode' in result:
                response = dict_merge(response, result)
            else:
                response['body'] = result
        except exceptions.HttpException as err:
            logger.error('HttpException', exc_info=True)
            response['statusCode'] = err.status
            response['body'] = err.body
        response['body'] = format_result(response['body'])
        logger.info('Response: %s', json.dumps(response, default=str))
        logger.debug('Response Body: %s', response['body'])
        return response

    return wrapper_decorator


def states_decorator(func):
    """
    Decorator for step function lambda function handlers

    Logs incoming event and response
    """
    @functools.wraps(func)
    def wrapper_decorator(event, context=None):
        logger.info('Event: %s', json.dumps(event, default=str))
        if event.get('scanId'):
            update_log_format(f'[%(levelname)s] %(asctime)s %(filename)s:%(funcName)s [ scanId: {event.get("scanId")} ] : %(message)s')
        result = func(event, context)
        logger.info('Result: %s', json.dumps(result, default=str))
        return result
    return wrapper_decorator
