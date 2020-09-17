import io
import json
import os
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import Decimal
from botocore.stub import Stubber

from lib.dynamodb import accounts_table, ncr_table, scans_table, scores_table
from lib.dynamodb.scans import ScansTable
from lib.s3.s3_buckets import S3
from states.cloudsploit import cloudsploit_populate, cloudsploit_setup, cloudsploit_error

@pytest.fixture(scope='function')
def s3_stubber():
    with Stubber(S3) as stubber:
        yield stubber

@pytest.fixture(scope='module')
def regular_account():
    account = {
        'accountId': '500',
        'account_name': 'blue',
    }
    accounts_table.put_item(Item=account)
    yield account
    accounts_table.delete_item(Key={'accountId': account['accountId']})

@pytest.fixture(scope='module')
def special_account():
    account = {
        'accountId': '600',
        'account_name': 'green',
        'scorecard_profile': 'special',
    }
    accounts_table.put_item(Item=account)
    yield account
    accounts_table.delete_item(Key={'accountId': account['accountId']})


def create_cloudsploit_data(collection, findings):
    return {
        'collectionData': {
            'aws': collection,
        },
        'resultsData': findings
    }


def create_cloudsploit_s3_response(cs_data):
    return {
        'Body': io.StringIO(json.dumps(cs_data)),
        'LastModified': datetime.now()
    }


class TestCloudSploitPopulate:
    @patch('lib.dynamodb.requirements_table.get_cloudsploit_based_requirements')
    def test_populate(self, get_cs_requirements, s3_stubber, regular_account):
        cs_data = create_cloudsploit_data({}, [
            {
                'plugin': 'pluginNameOne',
                'category': 'S3',
                'title': 'Plugin Name One',
                'resource': 'arn:aws:s3:::aaa-aaa-aaa-aaa',
                'region': 'global',
                'status': 'FAIL',
                'statusNumber': 2,
                'message': 'sample text'
            },
            {
                'plugin': 'pluginNameOne',
                'category': 'S3',
                'title': 'Plugin Name Two',
                'resource': 'arn:aws:s3:::aaa-aaa-aaa-aaa',
                'region': 'global',
                'status': 'FAIL',
                'statusNumber': 2,
                'message': 'sample text'
            },
            {
                'plugin': 'pluginNameOne',
                'category': 'S3',
                'title': 'Plugin Name Two',
                'resource': 'arn:aws:s3:::aaa-aaa-aaa-aaa',
                'region': 'global',
                'status': 'FAIL',
                'statusNumber': 2,
                'message': 'sample text2'
            },
        ])

        get_cs_requirements.return_value = [{
            'requirementId': '10',
            'weight': Decimal(100),
            'description': 'sample text',
            'source': 'cloudsploit',
            'severity': 'medium',
            'service': 'organizations',
            'component': 'account',
            'cloudsploit': {
                'finding': [
                    'Plugin Name One',
                    'Plugin Name Two',
                ]
            }
        }]
        s3_stubber.add_response('get_object', create_cloudsploit_s3_response(cs_data), {
            'Bucket': os.getenv('CLOUDSPLOIT_RESULT_BUCKET'),
            'Key': os.getenv('CLOUDSPLOIT_PREFIX') + '/' + regular_account['accountId'] + '/latest.json',
        })
        scan_id = scans_table.create_new_scan_id()

        cloudsploit_populate({'scanId': scan_id, 'accountId': regular_account['accountId']}, {})

        # check NCR record is created
        ncr_records_in_db = ncr_table.query_all(KeyConditionExpression=Key('scanId').eq(scan_id))

        for record in ncr_records_in_db:
            assert record.pop('ttl')
        assert ncr_records_in_db == [
            ncr_table.new_ncr_record({
                'accountId': regular_account['accountId'],
                'accountName': regular_account['account_name'],
                'cloudsploitStatus': 'FAIL',
                'requirementId': '10',
                'resourceId': 'aaa-aaa-aaa-aaa',
                'resourceType': 'organizations-account',
                'region': 'global',
                'reason': 'sample text\nsample text2',
            }, scan_id)
        ]

        # check score record is created
        score_records_in_db = scores_table.query_all(KeyConditionExpression=Key('scanId').eq(scan_id))

        for record in score_records_in_db:
            assert record.pop('ttl')
        assert score_records_in_db == [
            scores_table.new_score(
                scan_id,
                regular_account['accountId'],
                {
                    'requirementId': '10',
                    'severity': 'medium',
                    'weight': Decimal(100)
                },
                Decimal(3)
            )
        ]

    @patch('lib.dynamodb.requirements_table.get_cloudsploit_based_requirements')
    def test_cloudsploit_sourced_num_resources(self, get_cs_requirements, s3_stubber, regular_account):
        cs_data = create_cloudsploit_data({
            'ec2': {
                'describeInstances': {
                    'us-east-1': {
                        'data': [
                            {'instance': 1}, {'instance': 2}
                        ]
                    },
                    'us-west-2': {
                        'data': [
                            {'instance': 1}, {'instance': 2}
                        ]
                    },
                    'me-west-1': {
                        'data': [],
                        'err': 'region not enabled'
                    }
                }
            }
        }, [
            {
                'plugin': 'pluginNameOne',
                'category': 'S3',
                'title': 'Plugin Name One',
                'resource': 'arn:aws:s3:::aaa-aaa-aaa-aaa',
                'region': 'global',
                'status': 'FAIL',
                'statusNumber': 2,
                'message': 'sample text'
            },
        ])

        get_cs_requirements.return_value = [{
            'requirementId': '10',
            'weight': Decimal(100),
            'description': 'sample text',
            'source': 'cloudsploit',
            'severity': 'medium',
            'service': 'organizations',
            'component': 'account',
            'cloudsploit': {
                'finding': 'Plugin Name One',
                'source': 'ec2.describeInstances',
            }
        }]
        s3_stubber.add_response('get_object', create_cloudsploit_s3_response(cs_data), {
            'Bucket': os.getenv('CLOUDSPLOIT_RESULT_BUCKET'),
            'Key': os.getenv('CLOUDSPLOIT_PREFIX') + '/' + regular_account['accountId'] + '/latest.json',
        })
        scan_id = scans_table.create_new_scan_id()

        cloudsploit_populate({'scanId': scan_id, 'accountId': regular_account['accountId']}, {})

        # check NCR record is created
        ncr_records_in_db = ncr_table.query_all(KeyConditionExpression=Key('scanId').eq(scan_id))

        for record in ncr_records_in_db:
            assert record.pop('ttl')
        assert ncr_records_in_db == [
            ncr_table.new_ncr_record({
                'accountId': regular_account['accountId'],
                'accountName': regular_account['account_name'],
                'cloudsploitStatus': 'FAIL',
                'requirementId': '10',
                'resourceId': 'aaa-aaa-aaa-aaa',
                'resourceType': 'organizations-account',
                'region': 'global',
                'reason': 'sample text',
            }, scan_id)
        ]

        # check score record is created
        score_records_in_db = scores_table.query_all(KeyConditionExpression=Key('scanId').eq(scan_id))

        for record in score_records_in_db:
            assert record.pop('ttl')
        assert score_records_in_db == [
            scores_table.new_score(
                scan_id,
                regular_account['accountId'],
                {
                    'requirementId': '10',
                    'severity': 'medium',
                    'weight': Decimal(100)
                },
                Decimal(4)
            )
        ]

    @patch('lib.dynamodb.requirements_table.get_cloudsploit_based_requirements')
    def test_populate_na_requirement(self, get_cs_requirements, s3_stubber, special_account):
        """Test populate with requirement that doesn't apply to account"""
        cs_data = create_cloudsploit_data({}, [
            {
                'plugin': 'pluginNameOne',
                'category': 'S3',
                'title': 'Plugin Name One',
                'resource': 'arn:aws:s3:::aaa-aaa-aaa-aaa',
                'region': 'global',
                'status': 'FAIL',
                'statusNumber': 2,
                'message': 'sample text'
            },
        ])

        get_cs_requirements.return_value = [{
            'requirementId': '10',
            'weight': Decimal(100),
            'description': 'sample text',
            'source': 'cloudsploit',
            'severity': 'medium',
            'onlyAppliesTo': ['other-than-special'],
            'cloudsploit': {
                'finding': 'Plugin Name One'
            }
        }]
        s3_stubber.add_response('get_object', create_cloudsploit_s3_response(cs_data), {
            'Bucket': os.getenv('CLOUDSPLOIT_RESULT_BUCKET'),
            'Key': os.getenv('CLOUDSPLOIT_PREFIX') + '/' + special_account['accountId'] + '/latest.json',
        })
        scan_id = scans_table.create_new_scan_id()

        cloudsploit_populate({'scanId': scan_id, 'accountId': special_account['accountId']}, {})

        # check NCR record is created
        ncr_records_in_db = ncr_table.query_all(KeyConditionExpression=Key('scanId').eq(scan_id))

        assert ncr_records_in_db == []

        # check score record is created
        score_records_in_db = scores_table.query_all(KeyConditionExpression=Key('scanId').eq(scan_id))

        for record in score_records_in_db:
            assert record.pop('ttl')
        assert score_records_in_db == [
            scores_table.new_score(
                scan_id,
                special_account['accountId'],
                {
                    'requirementId': '10',
                    'severity': 'medium',
                    'weight': Decimal(100)
                },
                scores_table.NOT_APPLICABLE,
                scores_table.NOT_APPLICABLE,
            )
        ]


class TestCloudSploitSetup():
    event = {
        'accountId': '100',
        'scanId': scans_table.create_new_scan_id(),
        'cloudsploitSettingsMap': {
            'default': {
                'key1': 'value1'
            },
            'settings1': {
                'key_1': 'value_1'
            }
        }
    }

    def test_setting_selection(self):
        """Tests the logic for setting up cloudsploit and returns the required error or cloudsploit settings"""

        account = {
            'accountId': '100',
            'cross_account_role': 'arn:aaa',
            'scorecard_profile': 'settings1'
        }

        desired_output = {
            'cloud': 'aws',
            'cloudConfig': {'roleArn': 'arn:aaa'},
            'settings': {
                'key_1': 'value_1'
            },
            's3Prefix': '100'
        }

        accounts_table.put_item(Item=account)
        output = cloudsploit_setup(self.event, None)
        accounts_table.delete_item(Key={'accountId': account['accountId']})
        assert output == desired_output

    def test_default_settings(self):
        account = {
            'accountId': '100',
            'cross_account_role': 'arn:aaa',
        }
        expected_result = {
            'cloud': 'aws',
            'cloudConfig': {'roleArn': 'arn:aaa'},
            'settings': {
                'key1': 'value1'
            },
            's3Prefix': '100'
        }

        accounts_table.put_item(Item=account)
        output = cloudsploit_setup(self.event, None)
        accounts_table.delete_item(Key={'accountId': account['accountId']})
        assert output == expected_result

    def test_no_cross_account_role(self):
        account = {
            'accountId': '100',
            'scorecard_profile': 'settings1'
        }

        accounts_table.put_item(Item=account)
        with pytest.raises(ValueError):
            cloudsploit_setup(self.event, None)
        accounts_table.delete_item(Key={'accountId': account['accountId']})

    def test_invalid_setting(self):
        account = {
            'accountId': '100',
            'cross_account_role': 'arn:aaa',
            'scorecard_profile': 'settingNotPresent',
        }

        accounts_table.put_item(Item=account)
        with pytest.raises(KeyError):
            cloudsploit_setup(self.event, None)
        accounts_table.delete_item(Key={'accountId': account['accountId']})

class TestCloudSploitError():
    context = SimpleNamespace()
    context.function_name = 'function-name'

    @patch('lib.dynamodb.requirements_table.get_cloudsploit_based_requirements')
    def test_add_dnc_score(self, get_cs_requirements, regular_account):
        """Tests adding scores for account/requirement"""
        scan_id = ScansTable.create_new_scan_id()
        event = {
            'scanId': scan_id,
            'accountId': regular_account['accountId'],
            'error': {
                'Cause': json.dumps({'message': 'Test Error'})
            },
        }

        get_cs_requirements.return_value = [{
            'requirementId': '10',
            'weight': Decimal(100),
            'description': 'sample text',
            'source': 'cloudsploit',
            'severity': 'medium',
            'cloudsploit': {
                'finding': 'Plugin Name One'
            }
        }]
        cloudsploit_error(event, self.context)

        expected_results = {
            'accountId': regular_account['accountId'],
            'score': {
                'medium': {
                    'numFailing': scores_table.DATA_NOT_COLLECTED,
                    'numResources': scores_table.DATA_NOT_COLLECTED,
                    'weight': Decimal('100'),
                }
            },
            'requirementId': '10',
            'scanId': scan_id,
            'accntId_rqrmntId': f'{regular_account["accountId"]}#10'}
        result = scores_table.get_item(Key={'scanId': scan_id, 'accntId_rqrmntId': f'{regular_account["accountId"]}#10'})['Item']
        assert result.pop('ttl')
        assert result == expected_results

    @patch('lib.dynamodb.requirements_table.get_cloudsploit_based_requirements')
    def test_add_not_applicable_score(self, get_cs_requirements, special_account):
        """Tests adding N/A scores to the scores-table for requirements not applying to the account"""
        scan_id = ScansTable.create_new_scan_id()
        event = {
            'scanId': scan_id,
            'accountId': special_account['accountId'],
            'error': {
                'Cause': json.dumps({'message': 'Test Error'})
            },
        }

        get_cs_requirements.return_value = [{
            'requirementId': '10',
            'weight': Decimal(100),
            'description': 'sample text',
            'source': 'cloudsploit',
            'severity': 'medium',
            'onlyAppliesTo': ['other-special'],
            'cloudsploit': {
                'finding': 'Plugin Name One'
            }
        }]
        cloudsploit_error(event, self.context)

        expected_results = {
            'accountId': special_account['accountId'],
            'score': {
                'medium': {
                    'numFailing': scores_table.NOT_APPLICABLE,
                    'numResources': scores_table.NOT_APPLICABLE,
                    'weight': Decimal('100'),
                }
            },
            'requirementId': '10',
            'scanId': scan_id,
            'accntId_rqrmntId': f'{special_account["accountId"]}#10'}
        result = scores_table.get_item(Key={'scanId': scan_id, 'accntId_rqrmntId': f'{special_account["accountId"]}#10'})['Item']
        assert result.pop('ttl')
        assert result == expected_results

    @patch('lib.dynamodb.requirements_table.get_cloudsploit_based_requirements')
    def test_adds_error_to_scan(self, get_cs_requirements, regular_account):
        scan_id = ScansTable.create_new_scan_id()
        event = {
            'scanId': scan_id,
            'accountId': regular_account['accountId'],
            'error': {
                'Cause': json.dumps({'message': 'Test Error'})
            },
        }
        get_cs_requirements.return_value = [{
            'requirementId': '10',
            'weight': Decimal(100),
            'description': 'sample text',
            'source': 'cloudsploit',
            'severity': 'medium',
            'cloudsploit': {
                'finding': 'Plugin Name One'
            }
        }]

        cloudsploit_error(event, self.context)

        expected_results = {
            'scan': ScansTable.SCAN,
            'scanId': scan_id,
            'errors': [{
                'error': {
                    'Cause': {
                        'message': 'Test Error',
                        'trace': None,
                    },
                },
                'functionName': 'function-name',
            }]
        }
        assert scans_table.get_item(Key={'scan': ScansTable.SCAN, 'scanId': scan_id})['Item'] == expected_results
