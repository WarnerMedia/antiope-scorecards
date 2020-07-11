import os
import logging

BASE_FORMAT_STRING = '[%(levelname)s] %(asctime)s %(filename)s:%(funcName)s : %(message)s'

root_logger = logging.getLogger()
logger = logging.getLogger('scorecards')

logger.setLevel(os.getenv('LOG_LEVEL', 'DEBUG'))

if not os.environ.get('AWS_EXECUTION_ENV'):
    root_handler = logging.StreamHandler()
    root_handler.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(root_handler)


def update_log_format(format_string):
    prefix = '%(aws_request_id)s ' if os.environ.get('AWS_EXECUTION_ENV') else ''
    suffix = '\n' if os.environ.get('AWS_EXECUTION_ENV') else ''
    for handler in root_logger.handlers:
        handler.setFormatter(logging.Formatter(prefix + format_string + suffix))

update_log_format(BASE_FORMAT_STRING)
