from functools import wraps

from lib.logger import logger
from lib.dynamodb import scans_table

def get_scan_id_decorator(func):
    @wraps(func)
    def wrapper(event, context):
        scan_id = scans_table.get_latest_complete_scan()
        logger.debug('Latest completed scan: %s', scan_id)
        # add to event object
        event['scanId'] = scan_id
        response = func(event, context)
        # add to reponse from lambda
        response['scanId'] = scan_id

        return response

    return wrapper
