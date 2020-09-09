"""
-file concerned with implementation of GET /scans
-should return as many scans as possible starting from newest
-return size must be capped at 6mb
"""
from boto3.dynamodb.conditions import Key

from lib.dynamodb import scans_table
from lib.lambda_decorator.decorator import api_decorator, format_result

BYTE_LIMIT = 5000000


def determine_bytes(target: dict) -> int:
    target_with_formatting = format_result(target)
    return len(target_with_formatting.encode('utf-8'))


def make_result(records: list) -> dict:
    for record in records:
        record.pop('scan', None)  # omit 'scan' from result, if key is present.
    return {'scans': records}


def make_max_return(records: list, byte_limit: int) -> list:
    count_bytes = determine_bytes(make_result(records))
    while count_bytes > byte_limit:
        records.pop()
        count_bytes = determine_bytes(make_result(records))
    return make_result(records)


@api_decorator
def scans_handler(event, context):
    records = scans_table.query_all(
        KeyConditionExpression=Key('scan').eq(scans_table.SCAN),
        ScanIndexForward=False
    )
    return make_max_return(records, BYTE_LIMIT)
