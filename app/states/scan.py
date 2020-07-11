"""
Lambda function handler for scan related steps
OpenScan, CloseScan, and ScanError
"""
import time

from lib.dynamodb import scans_table
from lib.lambda_decorator.decorator import states_decorator


@states_decorator
def open_handler(event, context):
    """
    Adds a new entry to scans-table with a randomly generated scan_id and TTL of 30 days

    Expected input event format
    {}
    """
    scan_id = scans_table.create_new_scan_id()
    scans_table.put_item(
        Item={
            'scan': scans_table.SCAN,
            'processState': scans_table.IN_PROGRESS,
            'scanId': scan_id,
            'ttl': int(time.time()) + 2592000,  # Adding 30 days to current time
        }
    )

    return {
        'processState': scans_table.IN_PROGRESS,
        'scanId': scan_id,
    }


@states_decorator
def close_handler(event, context):
    """
    Updates the specific scan_id entry in scans-table to completed

    Expected input event format
    {
        "scanId": scan_id
    }
    """
    scan_id = event['openScan']['scanId']

    scans_table.update_item(
        Key={'scan': scans_table.SCAN, 'scanId': scan_id},
        UpdateExpression='SET processState = :updated_state',
        ExpressionAttributeValues={':updated_state': scans_table.COMPLETED},
        ReturnValues='UPDATED_NEW',
    )

    return {}


@states_decorator
def error_handler(event, context):
    """
    Updates the specific scan_id entry status to error
    and records error details

    Expected input event format
    {
        "scanId": scan_id,
        "scanError": error from step function
    }
    """
    scan_id = event['openScan']['scanId']
    scan_error = event['scanError']
    scans_table.add_error(scan_id, context.function_name, scan_error, is_fatal=True)

    return {}
