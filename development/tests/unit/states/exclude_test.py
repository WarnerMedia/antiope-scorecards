from unittest.mock import Mock, patch
from functools import partial

from boto3.dynamodb.conditions import Key

from lib.dynamodb import ncr_table, scans_table
from states import exclude


class TestExcludeStepHandler:

    exclusion_types_effective_initial = {'Approval': {'states': {'initial': {'effective': True}}}}
    exclusion_types_not_effective_initial = {'Approval': {'states': {'initial': {'effective': False}}}}

    def test_group_exclusions(self):
        exclusions = [
            {
                'requirementId': 'aaa',
                'accountId': '*',
                'resourceId': 'arn:aws:*:*',
            },
            {
                'requirementId': 'aaa',
                'accountId': '222',
                'resourceId': 'arn:aws:*',
            },
            {
                'requirementId': 'bbb',
                'accountId': '*',
                'resourceId': 'arn:*',
            },
            {
                'requirementId': 'bbb',
                'accountId': '222',
                'resourceId': 'arn:*',
            },
        ]
        grouped_exclusions = exclude.group_exclusions(exclusions)
        assert grouped_exclusions == {
            'aaa': {
                '*': [exclusions[0]],
                '222': [exclusions[1]],
            },
            'bbb': {
                '*': [exclusions[2]],
                '222': [exclusions[3]],
            }
        }

    def test_exclusion_prioritizer(self):
        # tests weight of exclusions by putting them in the right order
        exclusions = [
            {'status': 'rejected', 'accountId': 'x', 'resourceId': 'arn:x', 'expirationDate': '2999/12/31'},
            {'status': 'rejected', 'accountId': 'x', 'resourceId': 'arn:*', 'expirationDate': '2999/12/31'},
            {'status': 'rejected', 'accountId': '*', 'resourceId': 'arn:x', 'expirationDate': '2999/12/31'},
            {'status': 'rejected', 'accountId': '*', 'resourceId': 'arn:*', 'expirationDate': '2999/12/31'},
            {'status': 'approved', 'accountId': 'x', 'resourceId': 'arn:x', 'expirationDate': '2999/12/31'},
            {'status': 'approved', 'accountId': 'x', 'resourceId': 'arn:*', 'expirationDate': '2999/12/31'},
            {'status': 'approved', 'accountId': '*', 'resourceId': 'arn:x', 'expirationDate': '2999/12/31'},
            {'status': 'approved', 'accountId': '*', 'resourceId': 'arn:*', 'expirationDate': '2999/12/31'},
        ]

        partial_exclusion_prioritizer = partial(exclude.exclusion_prioritizer, self.exclusion_types_not_effective_initial)
        sorted_exclusions = sorted(exclusions, key=partial_exclusion_prioritizer)

        for e in sorted_exclusions:
            print(e)

        assert sorted_exclusions == [
            {'status': 'approved', 'accountId': '*', 'resourceId': 'arn:*', 'expirationDate': '2999/12/31'},
            {'status': 'approved', 'accountId': '*', 'resourceId': 'arn:x', 'expirationDate': '2999/12/31'},
            {'status': 'approved', 'accountId': 'x', 'resourceId': 'arn:*', 'expirationDate': '2999/12/31'},
            {'status': 'approved', 'accountId': 'x', 'resourceId': 'arn:x', 'expirationDate': '2999/12/31'},
            {'status': 'rejected', 'accountId': '*', 'resourceId': 'arn:*', 'expirationDate': '2999/12/31'},
            {'status': 'rejected', 'accountId': '*', 'resourceId': 'arn:x', 'expirationDate': '2999/12/31'},
            {'status': 'rejected', 'accountId': 'x', 'resourceId': 'arn:*', 'expirationDate': '2999/12/31'},
            {'status': 'rejected', 'accountId': 'x', 'resourceId': 'arn:x', 'expirationDate': '2999/12/31'},
        ]

    def test_is_effective(self):
        approved_not_expired = {
            'expirationDate': '2999/12/31',
            'status': 'approved',
        }

        initial_not_expired = {
            'expirationDate': '2999/12/31',
            'status': 'initial',
            'type': 'Approval',
            'requirementId': '1',
            'accountId': '2',
            'resourceId': '3'
        }

        approved_expired = {
            'expirationDate': '2000/12/31',
            'status': 'approved',
            'type': 'Approval',
            'requirementId': '1',
            'accountId': '2',
            'resourceId': '3'
        }

        not_approved_expired = {
            'expirationDate': '2000/12/31',
            'status': 'rejected',
            'type': 'Approval',
            'requirementId': '1',
            'accountId': '2',
            'resourceId': '3'
        }

        malformed_1 = {}
        malformed_2 = {'requirementId': '1', 'accountId': '2', 'resourceId': '3'}

        assert exclude.is_effective(self.exclusion_types_not_effective_initial, approved_not_expired) is True
        assert exclude.is_effective(self.exclusion_types_not_effective_initial, initial_not_expired) is False
        assert exclude.is_effective(self.exclusion_types_effective_initial, initial_not_expired) is True
        assert exclude.is_effective(self.exclusion_types_not_effective_initial, approved_expired) is False
        assert exclude.is_effective(self.exclusion_types_not_effective_initial, not_approved_expired) is False
        assert exclude.is_effective(self.exclusion_types_not_effective_initial, malformed_1) is False
        assert exclude.is_effective(self.exclusion_types_not_effective_initial, malformed_2) is False

    def test_pick_exclusion(self):
        exclusions = [
            {'status': 'rejected', 'accountId': 'x', 'resourceId': 'arn:x', 'expirationDate': '2999/12/31'},
            {'status': 'approved', 'accountId': '*', 'resourceId': 'arn:*', 'expirationDate': '2999/12/31'},
        ]
        exclusion_types = {'Approval': {'states': {'initial': {'effective': False}}}}
        partial_exclusion_prioritizer = partial(exclude.exclusion_prioritizer, exclusion_types)
        assert exclude.pick_exclusion(exclusions, partial_exclusion_prioritizer) == exclusions[1]
        assert exclude.pick_exclusion([], partial_exclusion_prioritizer) == {}

    def test_match_exclusions(self):
        ncr = {
            'requirementId': 'req1',
            'accountId': '111',
            'resourceId': 'arn:aws:some:resource'
        }
        grouped_exclusions = {
            'req1': {
                '*': [{
                    'requirementId': 'req1',
                    'accountId': '*',
                    'resourceId': 'arn:aws:some:resource',
                    'status': 'sample_status'
                }],
                '111': [{
                    'requirementId': 'req1',
                    'accountId': '111',
                    'resourceId': 'arn:aws:some:resource*',
                    'status': 'sample_status'
                }, {
                    'requirementId': 'req1',
                    'accountId': '111',
                    'resourceId': 'arn:aws:some:other*',
                    'status': 'sample_status'
                }],
                '222': [{
                    'requirementId': 'req1',
                    'accountId': '222',
                    'resourceId': 'arn:aws:some:resource*',
                    'status': 'sample_status'
                }],
            },
            'req2': {
                '*': [{
                    'requirementId': 'req2',
                    'accountId': '*',
                    'resourceId': 'arn:aws:some:resource',
                    'status': 'sample_status'
                }],
                '111': [{
                    'requirementId': 'req2',
                    'accountId': '111',
                    'resourceId': 'arn:aws:some:partial*',
                    'status': 'sample_status'
                }],
            }
        }
        assert exclude.match_exclusions(ncr, grouped_exclusions) == [
            {
                'requirementId': 'req1',
                'accountId': '*',
                'resourceId': 'arn:aws:some:resource',
                'status': 'sample_status'
            }, {
                'requirementId': 'req1',
                'accountId': '111',
                'resourceId': 'arn:aws:some:resource*',
                'status': 'sample_status'
            }
        ]


    def test_update_ncr(self):
        ncr = {
            'scanId': 'EXCLUSIONTESTID',
            'accntId_rsrceId_rqrmntId': '12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
            'accountId': '1234578901',
            'accountName': 'TEST ACCOUNT NAME',
            'requirementId': 'requirementId01',
            'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
            'rqrmntId_accntId': 'requirementId01_12345678901',
        }
        exclusion = {
            'accountId': '12345678901',
            'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
            'requirementId': 'requirementId04',
            'rqrmntId_rsrceRegex': 'requirementId04_arn:aws:lambda:us-west-2:12345678901:function:test-function',
            'status': 'approved',
            'expirationDate': '2999/12/13',
            'reason': 'TESTING',
            'type': 'TESTING',
            'hidesResources': False
        }
        assert exclude.update_ncr_exclusion(ncr, exclusion, self.exclusion_types_not_effective_initial) == {
            'scanId': 'EXCLUSIONTESTID',
            'accntId_rsrceId_rqrmntId': '12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
            'accountId': '1234578901',
            'accountName': 'TEST ACCOUNT NAME',
            'requirementId': 'requirementId01',
            'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
            'rqrmntId_accntId': 'requirementId01_12345678901',
            'isHidden': False,
            'exclusionApplied': True,
            'exclusion': exclusion
        }


    # patch the exclusion query
    # ncr query can be written to database
    @patch('lib.dynamodb.exclusions_table.scan_all')
    def test_exclude_handler(self, exclusions_mock: Mock):
        scan_id = scans_table.create_new_scan_id()
        ncr = {
            'scanId': scan_id,
            'accntId_rsrceId_rqrmntId': '12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
            'accountId': '1234578901',
            'accountName': 'TEST ACCOUNT NAME',
            'requirementId': 'requirementId01',
            'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
            'rqrmntId_accntId': 'requirementId01_12345678901',
        }
        ncr_table.put_item(Item=ncr)

        exclusions_mock.return_value = [
            {
                'status': 'rejected',
                'accountId': '*',
                'requirementId': 'requirementId02',
                'resourceId': '*',
                'expirationDate': '2999/12/31'
            },
            {
                'status': 'rejected',
                'accountId': '1234578901',
                'requirementId': 'requirementId01',
                'resourceId': 'arn:aws:lambda:*',
                'expirationDate': '2999/12/31'
            },
            {
                'status': 'approved',
                'accountId': '*',
                'requirementId': 'requirementId01',
                'resourceId': 'arn:aws:lambda:*',
                'expirationDate': '2999/12/31',
                'reason': 'inspected looks fine',
                'type': 'justification',
            },
        ]

        event = {'openScan': {'scanId': scan_id}}
        assert exclude.exclude_handler(event, {}) is None
        updated_ncrs = sorted(
            ncr_table.query_all(KeyConditionExpression=Key('scanId').eq(scan_id)),
            key=lambda x: x['requirementId'],
        )

        expected_ncrs = [exclude.update_ncr_exclusion(ncr, exclusions_mock.return_value[2], self.exclusion_types_effective_initial)]

        assert updated_ncrs == expected_ncrs
