"""
unit tests for s3importer.py
"""
import io
import json
import random
from unittest.mock import patch
from datetime import datetime

import pytest
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import Decimal
from botocore.stub import Stubber, ANY

from lib.dynamodb import ncr_table, scores_table, scans_table
from lib.s3.s3_buckets import S3
from states.s3importer import s3import_handler


@pytest.fixture(scope='function')
def s3_stubber():
    with Stubber(S3) as stubber:
        yield stubber


def create_s3_response(s3_data):
    return {
        'Body': io.StringIO(json.dumps(s3_data)),
        'LastModified': datetime.now()
    }


def create_s3_data(account_ids, resource_count, req_id):
    return {
        account_id: {
            'totalResourceCount': resource_count,
            'failingResources': [
                {
                    'accountId': account_id,
                    'accountName': str(account_id) + '_account_name',
                    'requirementId': req_id,
                    'resourceId': ''.join(random.choice(['a', 'b', 'c', 'd']) for _ in range(5)),
                    'resourceType': 'ec2',
                    'region': 'us-east-2',
                    'reason': 'no_reason'
                }
                for _ in range(resource_count - 1)  # there is always 1 passing resource
            ]
        }
        for account_id in account_ids
    }


def create_s3import_requirement(req_id, severity, s3_key):
    return {
        'requirementId': req_id,
        'description': 'sample text',
        'source': 's3Import',
        'severity': severity,
        'weight': {
            'info': 1,
            'low': 10,
            'medium': 100,
            'high': 1000,
            'critical': 10000
        }[severity],
        's3Import': {
            's3Key': s3_key,
            's3Bucket': 'sample_bucket'
        }
    }


class TestS3Importer:
    @patch('lib.dynamodb.requirements_table.get_item')
    def test_s3importer_single_failing_resource_ncr(self, get_item, s3_stubber):
        s3_key = 'sample key'
        requirement_id = '100'
        account_ids = ('1',)
        event = {
            'scanId': scans_table.create_new_scan_id(),
            'requirementId': requirement_id,
            'accountIds': [account_ids[0]],
        }
        s3_import_requirement = create_s3import_requirement(
            requirement_id, random.choice(['critical', 'high', 'medium', 'low', 'info']), s3_key
        )
        s3_data = create_s3_data(account_ids, 2, requirement_id)

        get_item.return_value = {
            'Item': s3_import_requirement
        }
        s3_stubber.add_response('get_object', create_s3_response(s3_data),
                                {
                                    'Bucket': ANY,
                                    'Key': s3_key
                                })

        s3import_handler(event, {})

        ncr_records_in_db = ncr_table.query(
            KeyConditionExpression=Key('scanId').eq(event['scanId'])
        )['Items']
        account_id = account_ids[0]
        resource_id = s3_data[account_id]['failingResources'][0]['resourceId']
        account_name = s3_data[account_id]['failingResources'][0]['accountName']
        reason = s3_data[account_ids[0]]['failingResources'][0]['reason']
        region = s3_data[account_ids[0]]['failingResources'][0]['region']
        resource_type = s3_data[account_ids[0]]['failingResources'][0]['resourceType']
        scan_id = event['scanId']

        for record in ncr_records_in_db:
            assert record.pop('ttl')
        assert ncr_records_in_db == [
            {
                'accntId_rsrceId_rqrmntId': f'{account_id}#{resource_id}#{requirement_id}',
                'rqrmntId_accntId': f'{requirement_id}#{account_id}',
                'accountId': account_id,
                'accountName': account_name,
                'reason': reason,
                'region': region,
                'requirementId': requirement_id,
                'resourceId': resource_id,
                'scanId': scan_id,
                'resourceType': resource_type
            }
        ]

    @patch('lib.dynamodb.requirements_table.get_item')
    def test_s3importer_single_resource_score(self, get_item, s3_stubber):
        s3_key = 'sample key'
        requirement_id = '100'
        account_ids = ('1',)
        event = {
            'scanId': scans_table.create_new_scan_id(),
            'requirementId': requirement_id,
            'accountIds': [account_ids[0]],
        }
        s3_import_requirement = create_s3import_requirement(
            requirement_id, 'critical', s3_key
        )
        s3_data = create_s3_data(account_ids, 2, requirement_id)

        get_item.return_value = {
            'Item': s3_import_requirement
        }
        s3_stubber.add_response('get_object', create_s3_response(s3_data), {'Bucket': ANY, 'Key': s3_key})

        s3import_handler(event, {})

        score_records_in_db = scores_table.query(
            KeyConditionExpression=Key('scanId').eq(event['scanId'])
        )['Items']
        for record in score_records_in_db:
            assert record.pop('ttl')

        account_id = account_ids[0]
        scan_id = event['scanId']
        assert score_records_in_db == [scores_table.new_score(
            scan_id,
            account_id,
            s3_import_requirement,
            Decimal(2),
        )]
