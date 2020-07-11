"""
unit tests for s3importer_error.py
"""
from datetime import datetime
from types import SimpleNamespace

import pytest
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import Decimal

from lib.dynamodb import requirements_table, scores_table, scans_table
from states.s3importer_error import s3import_error_handler

SCAN_ID = str(datetime.now().isoformat())

EVENT = {
    'scanId': SCAN_ID,
    'requirementId': '1',
    'accountIds': ['111', '222', '333'],
    'error': 'test-error'
}

DESIRED_OUTPUT = [
    scores_table.new_score(
        SCAN_ID,
        '111',
        {
            'requirementId': '1',
            'severity': 'high',
            'weight': Decimal(1000),
        },
        scores_table.DATA_NOT_COLLECTED,
        scores_table.DATA_NOT_COLLECTED,
    ),
    scores_table.new_score(
        SCAN_ID,
        '222',
        {
            'requirementId': '1',
            'severity': 'high',
            'weight': Decimal(1000),
        },
        scores_table.DATA_NOT_COLLECTED,
        scores_table.DATA_NOT_COLLECTED,
    ),
    scores_table.new_score(
        SCAN_ID,
        '333',
        {
            'requirementId': '1',
            'severity': 'high',
            'weight': Decimal(1000),
        },
        scores_table.DATA_NOT_COLLECTED,
        scores_table.DATA_NOT_COLLECTED,
    ),
]

def test_many_accounts():
    """
    comprehensive testcase for s3import error handler
    """
    requirements_table.put_item(
        Item={
            'requirementId': '1',
            'description': 'sample text',
            'source': 's3Import',
            'severity': 'high',
            'weight': 1000,
            's3Import': {
                's3Key': 'one',
                's3Bucket': 'mybucket'
            }
        }
    )
    context = SimpleNamespace()
    context.function_name = 'function-name'
    s3import_error_handler(EVENT, context)
    records_in_db = scores_table.query(
        KeyConditionExpression=Key('scanId').eq(EVENT['scanId']))['Items']
    for record in records_in_db:
        assert record.pop('ttl')

    sorted_handler_output = sorted(records_in_db, key=lambda k: k['accountId'])
    sorted_desired_output = sorted(DESIRED_OUTPUT, key=lambda k: k['accountId'])

    assert sorted_handler_output == sorted_desired_output

    expected_scans_table_results = {
        'scan': scans_table.SCAN,
        'scanId': SCAN_ID,
        'errors': [
            {
                'functionName': context.function_name,
                'error': 'test-error'
            }
        ]
    }

    assert scans_table.get_item(Key={'scan': scans_table.SCAN, 'scanId': SCAN_ID})['Item'] == expected_scans_table_results


def test_invalid_event():
    """
    test verifying that invalid events raise an exception for s3 import error handler
    """
    requirements_table.put_item(
        Item={
            'requirementId': '1',
            'description': 'sample text',
            'source': 's3Import',
            'severity': 'high',
            'weight': 1000,
            's3Import': {
                's3Key': 'one',
                's3Bucket': 'mybucket'
            }
        }
    )
    context = SimpleNamespace()
    context.function_name = 'function-name'
    invalid_event = {**EVENT}
    invalid_event['scanId'] = True
    with pytest.raises(TypeError):
        s3import_error_handler(invalid_event, context)
