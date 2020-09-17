import os
import logging

BASE_FORMAT_STRING = '[%(levelname)s] %(asctime)s %(filename)s:%(funcName)s : %(message)s'

root_logger = logging.getLogger()
logger = logging.getLogger('scorecards')

logger.setLevel(os.getenv('LOG_LEVEL', 'DEBUG'))

in_lambda = os.environ.get('AWS_EXECUTION_ENV', '').startswith('AWS_Lambda')

if not in_lambda:
    root_handler = logging.StreamHandler()
    root_handler.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(root_handler)


def update_log_format(format_string):
    prefix = '%(aws_request_id)s ' if in_lambda else ''
    suffix = '\n' if in_lambda else ''
    for handler in root_logger.handlers:
        handler.setFormatter(logging.Formatter(prefix + format_string + suffix))

update_log_format(BASE_FORMAT_STRING)
