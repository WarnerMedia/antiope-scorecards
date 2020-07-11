"""
unit test for app/states/score.py
"""
from unittest.mock import patch

from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import Decimal

from lib.dynamodb import account_scores_table, scans_table, scores_table, ncr_table


def create_requirement_definition(req_id):
    req_def = {
        'requirementId': req_id,
        'severity': 'low',
        'weight': Decimal(10)
    }
    return req_def


def create_score_record(account_id, req_def, scan_id, num_resources=1, is_dnc=False):
    score_record = scores_table.new_score(
        scan_id,
        account_id,
        req_def,
        num_resources=Decimal(num_resources) if not is_dnc else scores_table.DATA_NOT_COLLECTED,
        num_failing=None if not is_dnc else scores_table.DATA_NOT_COLLECTED
    )
    scores_table.put_item(Item=score_record)
    return score_record


def create_ncr_record(account_id, req_id, scan_id, resource_id='aaa'):
    ncr_record = {
        'accntId_rsrceId_rqrmntId': f'{account_id}#${resource_id}#{req_id}',
        'accountId': account_id,
        'accountName': 'yellow',
        'exclusionApplied': False,
        'reason': 'sample_text',
        'region': 'global',
        'requirementId': req_id,
        'resourceId': resource_id,
        'scanId': scan_id
    }
    ncr_table.put_item(Item=ncr_record)
    return ncr_record


class TestScoreCalc:
    @patch('lib.dynamodb.accounts_table.get_account')
    @patch('lib.dynamodb.requirements_table.scan_all')
    def test_score_calc_single_score_score(self, requirements_scan, get_account):
        scan_id = scans_table.create_new_scan_id()
        account_ids = ['55']
        account_id = account_ids[0]
        requirement_id = '11'
        event = {
            'openScan': {'scanId': scan_id},
            'load': {'accountIds': account_ids},
        }
        requirement_def = create_requirement_definition(requirement_id)
        create_score_record(account_id, requirement_def, scan_id)
        create_ncr_record(account_id, requirement_id, scan_id)

        requirements_scan.return_value = [requirement_def]
        get_account.return_value = {'account_name': 'An AWS Account'}
        from states.score import score_calc_handler # pylint: disable=import-outside-toplevel
        score_calc_handler(event, {})
        score_records_in_db = scores_table.query_all(
            KeyConditionExpression=Key('scanId').eq(event['openScan']['scanId'])
        )

        for record in score_records_in_db:
            assert record.pop('ttl')
        assert score_records_in_db == [
            {
                'scanId': scan_id,
                'accountId': account_id,
                'accntId_rqrmntId': f'{account_id}#{requirement_id}',
                'requirementId': requirement_id,
                'score': {
                    'low': {
                        'weight': Decimal(10),
                        'numResources': Decimal(1),
                        'numFailing': Decimal(1)
                    }
                }
            }
        ]

    @patch('lib.dynamodb.accounts_table.get_account')
    @patch('lib.dynamodb.requirements_table.scan_all')
    def test_score_calc_single_dnc_score_score(self, requirements_scan, get_account):
        scan_id = scans_table.create_new_scan_id()
        account_ids = ['55']
        account_id = account_ids[0]
        requirement_id = '11'
        event = {
            'openScan': {'scanId': scan_id},
            'load': {'accountIds': account_ids},
        }
        requirement_def = create_requirement_definition(requirement_id)
        create_score_record(account_id, requirement_def, scan_id, is_dnc=True)
        create_ncr_record(account_id, requirement_id, scan_id)

        requirements_scan.return_value = [requirement_def]
        get_account.return_value = {'account_name': 'An AWS Account'}
        from states.score import score_calc_handler # pylint: disable=import-outside-toplevel
        score_calc_handler(event, {})
        score_records_in_db = scores_table.query_all(
            KeyConditionExpression=Key('scanId').eq(event['openScan']['scanId'])
        )

        for record in score_records_in_db:
            assert record.pop('ttl')
        assert score_records_in_db == [
            {
                'scanId': scan_id,
                'accountId': account_id,
                'accntId_rqrmntId': f'{account_id}#{requirement_id}',
                'requirementId': requirement_id,
                'score': {
                    'low': {
                        'weight': 10,
                        'numResources': scores_table.DATA_NOT_COLLECTED,
                        'numFailing': scores_table.DATA_NOT_COLLECTED
                    }
                }
            }
        ]


    @patch('lib.dynamodb.accounts_table.get_account')
    @patch('lib.dynamodb.requirements_table.scan_all')
    def test_score_calc_single_score_account_score(self, requirements_scan, get_account):
        scan_id = scans_table.create_new_scan_id()
        account_ids = ['55']
        account_id = account_ids[0]
        requirement_id = '11'
        event = {
            'openScan': {'scanId': scan_id},
            'load': {'accountIds': account_ids},
        }
        requirement_def = create_requirement_definition(requirement_id)
        create_score_record(account_id, requirement_def, scan_id, num_resources=3)
        create_ncr_record(account_id, requirement_id, scan_id)
        create_ncr_record(account_id, requirement_id, scan_id, resource_id='bbb')
        create_ncr_record(account_id, requirement_id, scan_id, resource_id='ccc')

        requirements_scan.return_value = [requirement_def]
        get_account.return_value = {'account_name': 'An AWS Account'}

        from states.score import score_calc_handler # pylint: disable=import-outside-toplevel
        score_calc_handler(event, {})
        account_score_records_in_db = account_scores_table.get_item(
            Key={
                'accountId': account_id,
                'date': scan_id[0:10]
            }
        )['Item']

        assert account_score_records_in_db.pop('ttl')
        assert account_score_records_in_db == {
            'scanId': scan_id,
            'accountId': account_id,
            'accountName': 'An AWS Account',
            'date': scan_id[0:10],
            'score': {
                'low': {
                    'weight': Decimal(10),
                    'numResources': Decimal(3),
                    'numFailing': Decimal(3)
                },
            }
        }
