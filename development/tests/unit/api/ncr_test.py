import json

from unittest.mock import patch, Mock

from api import ncr
from api.ncr import prepare_allowed_actions_output
from lib.dynamodb import ncr_table, requirements_table, user_table, scans_table
from lib import ncr_util

user = 'my_user@test.com'
test_account_id = '12345678901'

def create_event():
    return {
        'queryStringParameters': {
            #'requirementId': 'abc'
        },
        'multiValueQueryStringParameters': {
            'accountId': [test_account_id]
        },
        'requestContext': {
            'authorizer': {
                'claims': {
                    'email': user,
                },
            },
        },
    }

def get_resource(exclusion=False):
    output = {}
    if exclusion:
        output['exclusion'] = {}
    return output


def get_requirement(remediation=False):
    output = {}
    if remediation:
        output['remediation'] = {}
    return output

def get_user(request_exclusion=False, trigger_remediation=False, admin_edit_exclusions=False, admin_add_exclusions=False):
    output = {
        'email': user,
        'accounts': {
            test_account_id: {
                'permissions':{}
            }
        },
    }
    if request_exclusion:
        output['accounts'][test_account_id]['permissions']['requestExclusion'] = True
    if trigger_remediation:
        output['accounts'][test_account_id]['permissions']['triggerRemediation'] = True
    return output


class TestNCR:
    ##User Level Permissions##
    @patch.object(ncr_util, 'get_allowed_actions')
    def test_prepare_actions_first(self, mock_get_allowed_actions: Mock):
        trunc_resource = get_resource(exclusion=False)
        trunc_requirement = get_requirement(remediation=False)
        trunc_user = get_user()
        output = prepare_allowed_actions_output({}, trunc_resource, trunc_user, test_account_id, trunc_requirement)
        assert output['allowedActions'] == mock_get_allowed_actions.return_value

    ############
    ####MOCK####
    ############
    #conditions: req cannot be remediated, user cannot request exclusion, user not an admin.
    @patch.object(scans_table, 'get_latest_complete_scan')
    @patch.object(user_table, 'get_user')
    @patch.object(requirements_table, 'scan_all')
    @patch.object(ncr_table, 'query_all')
    def test_get_ncr_without_permissions(self, mock_get_ncr, mock_get_requirement, mock_get_user, mock_get_latest_complete_scan):
        mock_get_user.return_value = {
            'email': user,
            'accounts': {},
        }
        mock_get_requirement.return_value = [
            {
                'severity': 'high',
                'description': 'All IAM Users have MFA enabled for Console Access',
                'weight': 1000,
                'source': 's3Import',
                'requirementId': 'requirementId01',
                's3Import':
                {
                    's3Bucket': 's3-req-bucket-01',
                    's3Key': 'req1'
                }
            }
        ]
        mock_get_latest_complete_scan.return_value = '2020-05-27T15:11:29.949427#wbnpjzzr'
        mock_get_ncr.return_value = [
            {
                'accountId': '12345678901',
                'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
                'exclusionApplied': True,
                'accountName': 'TEST ACCOUNT NAME',
                'scanId': '2020-05-27T15:11:29.949427#wbnpjzzr',
                'accntId_rsrceId_rqrmntId': '12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
                'exclusion': {
                    'accountId': '*',
                    'reason': 'inspected looks fine',
                    'resourceId': 'arn:aws:lambda:*',
                    'requirementId': 'requirementId01',
                    'type': 'justification',
                    'status': 'approved',
                    'expirationDate': '2999/12/31'
                },
                'requirementId': 'requirementId01',
                'rqrmntId_accntId': 'requirementId01_12345678901',
                # 'isHidden': False
            }
        ]
        resp = ncr.ncr_handler(create_event(), None)
        assert resp['statusCode'] == 403


    #conditions: req can be remediated, user can remediate, user cannot request exclusion, user not an admin.
    @patch.object(scans_table, 'get_latest_complete_scan')
    @patch.object(user_table, 'get_user')
    @patch.object(requirements_table, 'scan_all')
    @patch.object(ncr_table, 'query_all')
    def test_get_ncr_with_remediate(self, mock_get_ncr, mock_get_requirement, mock_get_user, mock_get_latest_complete_scan):
        mock_get_user.return_value = {
            'email': user,
            'accounts': {
                '12345678901':{
                    'permissions':{
                        'triggerRemediation':True
                    }
                }
            },
        }
        mock_get_requirement.return_value = [
            {
                'severity': 'high',
                'description': 'All IAM Users have MFA enabled for Console Access',
                'weight': 1000,
                'source': 's3Import',
                'requirementId': 'requirementId01',
                'remediation': {},
                's3Import':
                {
                    's3Bucket': 's3-req-bucket-01',
                    's3Key': 'req1'
                }
            }
        ]
        mock_get_latest_complete_scan.return_value = '2020-05-27T15:11:29.949427#wbnpjzzr'
        mock_get_ncr.return_value = [
            {
                'accountId': '12345678901',
                'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
                'exclusionApplied': True,
                'accountName': 'TEST ACCOUNT NAME',
                'scanId': '2020-05-27T15:11:29.949427#wbnpjzzr',
                'accntId_rsrceId_rqrmntId': '12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
                'exclusion': {
                    'accountId': '*',
                    'reason': 'inspected looks fine',
                    'resourceId': 'arn:aws:lambda:*',
                    'requirementId': 'requirementId01',
                    'type': 'justification',
                    'status': 'approved',
                    'expirationDate': '2999/12/31'
                },
                'requirementId': 'requirementId01',
                'rqrmntId_accntId': 'requirementId01_12345678901',
                'isHidden': False
            }
        ]
        resp = ncr.ncr_handler(create_event(), None)
        assert resp['statusCode'] == 200
        assert json.loads(resp['body']) == {
            'scanId': '2020-05-27T15:11:29.949427#wbnpjzzr',
            'ncrRecords': [{
                'ncrId': '2020-05-27T15:11:29.949427#wbnpjzzr#12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
                'allowedActions': {
                    'remediate': True,
                    'requestExclusion': False,
                    'requestExclusionChange': False
                },
                'resource': {
                    'accountId': '12345678901',
                    'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
                    'exclusionApplied': True,
                    'accountName': 'TEST ACCOUNT NAME',
                    'requirementId': 'requirementId01',
                    'isHidden': False,
                    'exclusion': {
                        'accountId': '*',
                        'reason': 'inspected looks fine',
                        'resourceId': 'arn:aws:lambda:*',
                        'requirementId': 'requirementId01',
                        'type': 'justification',
                        'status': 'approved',
                        'expirationDate': '2999/12/31'
                    },
                }
            }]
        }

    #conditions: req cannot be remediated, user can request exclusion, user not an admin.
    @patch.object(scans_table, 'get_latest_complete_scan')
    @patch.object(user_table, 'get_user')
    @patch.object(requirements_table, 'scan_all')
    @patch.object(ncr_table, 'query_all')
    def test_get_ncr_with_user_exclusion(self, mock_get_ncr, mock_get_requirement, mock_get_user, mock_get_latest_complete_scan):
        mock_get_user.return_value = {
            'email': user,
            'accounts': {
                '12345678901':{
                    'permissions':{
                        'triggerRemediation':True,
                        'requestExclusion':True
                    }
                }
            },
        }
        mock_get_requirement.return_value = [
            {
                'severity': 'high',
                'description': 'All IAM Users have MFA enabled for Console Access',
                'weight': 1000,
                'source': 's3Import',
                'requirementId': 'requirementId01',
                's3Import':
                {
                    's3Bucket': 's3-req-bucket-01',
                    's3Key': 'req1'
                }
            }
        ]
        mock_get_latest_complete_scan.return_value = '2020-05-27T15:11:29.949427#wbnpjzzr'
        mock_get_ncr.return_value = [
            {
                'accountId': '12345678901',
                'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
                'accountName': 'TEST ACCOUNT NAME',
                'scanId': '2020-05-27T15:11:29.949427#wbnpjzzr',
                'accntId_rsrceId_rqrmntId': '12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
                'requirementId': 'requirementId01',
                'rqrmntId_accntId': 'requirementId01_12345678901'
            }
        ]
        resp = ncr.ncr_handler(create_event(), None)
        assert resp['statusCode'] == 200
        assert json.loads(resp['body']) == {
            'scanId': '2020-05-27T15:11:29.949427#wbnpjzzr',
            'ncrRecords': [{
                'ncrId': '2020-05-27T15:11:29.949427#wbnpjzzr#12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
                'allowedActions': {
                    'remediate': False,
                    'requestExclusion': True,
                    'requestExclusionChange': False
                },
                'resource': {
                    'accountId': '12345678901',
                    'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
                    'accountName': 'TEST ACCOUNT NAME',
                    'requirementId': 'requirementId01',
                }
            }]
        }

    #conditions: req cannot be remediated, user cannot request exclusion, user is an admin with addWildCardExclusions.
    @patch.object(scans_table, 'get_latest_complete_scan')
    @patch.object(user_table, 'get_user')
    @patch.object(requirements_table, 'scan_all')
    @patch.object(ncr_table, 'query_all')
    def test_get_ncr_with_admin_exclusion(self, mock_get_ncr, mock_get_requirement, mock_get_user, mock_get_latest_complete_scan):
        mock_get_user.return_value = {
            'email': user,
            'accounts': {
            },
            'isAdmin': True,
        }
        mock_get_requirement.return_value = [
            {
                'severity': 'high',
                'description': 'All IAM Users have MFA enabled for Console Access',
                'weight': 1000,
                'source': 's3Import',
                'requirementId': 'requirementId01',
                's3Import':
                {
                    's3Bucket': 's3-req-bucket-01',
                    's3Key': 'req1'
                }
            }
        ]
        mock_get_latest_complete_scan.return_value = '2020-05-27T15:11:29.949427#wbnpjzzr'
        mock_get_ncr.return_value = [
            {
                'accountId': '12345678901',
                'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
                'accountName': 'TEST ACCOUNT NAME',
                'scanId': '2020-05-27T15:11:29.949427#wbnpjzzr',
                'accntId_rsrceId_rqrmntId': '12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
                'requirementId': 'requirementId01',
                'rqrmntId_accntId': 'requirementId01_12345678901',
            }
        ]
        resp = ncr.ncr_handler(create_event(), None)
        assert resp['statusCode'] == 200
        assert json.loads(resp['body']) == {
            'scanId': '2020-05-27T15:11:29.949427#wbnpjzzr',
            'ncrRecords': [{
                'ncrId': '2020-05-27T15:11:29.949427#wbnpjzzr#12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
                'allowedActions': {
                    'remediate': False,
                    'requestExclusion': True,
                    'requestExclusionChange': False
                },
                'resource': {
                    'accountId': '12345678901',
                    'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
                    'accountName': 'TEST ACCOUNT NAME',
                    'requirementId': 'requirementId01',
                }
            }]
        }

    #conditions: req cannot be remediated, user can request exclusion, user not an admin, req has an exclusion.
    @patch.object(scans_table, 'get_latest_complete_scan')
    @patch.object(user_table, 'get_user')
    @patch.object(requirements_table, 'scan_all')
    @patch.object(ncr_table, 'query_all')
    def test_get_ncr_with_user_exclusion_change(self, mock_get_ncr, mock_get_requirement, mock_get_user, mock_get_latest_complete_scan):
        mock_get_user.return_value = {
            'email': user,
            'accounts': {
                '12345678901':{
                    'permissions':{
                        'triggerRemediation':True,
                        'requestExclusion':True
                    }
                }
            },
        }
        mock_get_requirement.return_value = [
            {
                'severity': 'high',
                'description': 'All IAM Users have MFA enabled for Console Access',
                'weight': 1000,
                'source': 's3Import',
                'requirementId': 'requirementId01',
                's3Import':
                {
                    's3Bucket': 's3-req-bucket-01',
                    's3Key': 'req1'
                }
            }
        ]
        mock_get_latest_complete_scan.return_value = '2020-05-27T15:11:29.949427#wbnpjzzr'
        mock_get_ncr.return_value = [
            {
                'accountId': '12345678901',
                'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
                'exclusionApplied': True,
                'accountName': 'TEST ACCOUNT NAME',
                'scanId': '2020-05-27T15:11:29.949427#wbnpjzzr',
                'accntId_rsrceId_rqrmntId': '12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
                'requirementId': 'requirementId01',
                'rqrmntId_accntId': 'requirementId01_12345678901',
                'exclusion': {
                    'accountId': '*',
                    'reason': 'inspected looks fine',
                    'resourceId': 'arn:aws:lambda:*',
                    'requirementId': 'requirementId01',
                    'type': 'justification',
                    'status': 'approved',
                    'expirationDate': '2999/12/31'
                },
                'isHidden': False
            }
        ]
        resp = ncr.ncr_handler(create_event(), None)
        assert resp['statusCode'] == 200
        assert json.loads(resp['body']) == {
            'scanId': '2020-05-27T15:11:29.949427#wbnpjzzr',
            'ncrRecords': [{
                'ncrId': '2020-05-27T15:11:29.949427#wbnpjzzr#12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
                'allowedActions': {
                    'remediate': False,
                    'requestExclusion': False,
                    'requestExclusionChange': True
                },
                'resource': {
                    'accountId': '12345678901',
                    'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
                    'exclusionApplied': True,
                    'accountName': 'TEST ACCOUNT NAME',
                    'requirementId': 'requirementId01',
                    'exclusion': {
                        'accountId': '*',
                        'reason': 'inspected looks fine',
                        'resourceId': 'arn:aws:lambda:*',
                        'requirementId': 'requirementId01',
                        'type': 'justification',
                        'status': 'approved',
                        'expirationDate': '2999/12/31'
                    },
                    'isHidden': False,
                }
            }]
        }

    #conditions: req cannot be remediated, user cannot request exclusion, user is an admin, req has an exclusion.
    @patch.object(scans_table, 'get_latest_complete_scan')
    @patch.object(user_table, 'get_user')
    @patch.object(requirements_table, 'scan_all')
    @patch.object(ncr_table, 'query_all')
    def test_get_ncr_with_admin_exclusion_change(self, mock_get_ncr, mock_get_requirement, mock_get_user, mock_get_latest_complete_scan):
        mock_get_user.return_value = {
            'email': user,
            'accounts': {},
            'isAdmin': True,
        }
        mock_get_requirement.return_value = [
            {
                'severity': 'high',
                'description': 'All IAM Users have MFA enabled for Console Access',
                'weight': 1000,
                'source': 's3Import',
                'requirementId': 'requirementId01',
                's3Import':
                {
                    's3Bucket': 's3-req-bucket-01',
                    's3Key': 'req1'
                }
            }
        ]
        mock_get_latest_complete_scan.return_value = '2020-05-27T15:11:29.949427#wbnpjzzr'
        mock_get_ncr.return_value = [
            {
                'accountId': '12345678901',
                'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
                'exclusionApplied': True,
                'accountName': 'TEST ACCOUNT NAME',
                'scanId': '2020-05-27T15:11:29.949427#wbnpjzzr',
                'accntId_rsrceId_rqrmntId': '12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
                'requirementId': 'requirementId01',
                'rqrmntId_accntId': 'requirementId01_12345678901',
                'exclusion': {
                    'accountId': '*',
                    'reason': 'inspected looks fine',
                    'resourceId': 'arn:aws:lambda:*',
                    'requirementId': 'requirementId01',
                    'type': 'justification',
                    'status': 'approved',
                    'expirationDate': '2999/12/31'
                },
                'isHidden': False
            }
        ]
        resp = ncr.ncr_handler(create_event(), None)
        assert resp['statusCode'] == 200
        assert json.loads(resp['body']) == {
            'scanId': '2020-05-27T15:11:29.949427#wbnpjzzr',
            'ncrRecords': [{
                'ncrId': '2020-05-27T15:11:29.949427#wbnpjzzr#12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
                'allowedActions': {
                    'remediate': False,
                    'requestExclusion': False,
                    'requestExclusionChange': True
                },
                'resource': {
                    'accountId': '12345678901',
                    'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
                    'exclusionApplied': True,
                    'isHidden': False,
                    'accountName': 'TEST ACCOUNT NAME',
                    'requirementId': 'requirementId01',
                    'exclusion': {
                        'accountId': '*',
                        'reason': 'inspected looks fine',
                        'resourceId': 'arn:aws:lambda:*',
                        'requirementId': 'requirementId01',
                        'type': 'justification',
                        'status': 'approved',
                        'expirationDate': '2999/12/31'
                    },
                }
            }]
        }

    #conditions: req cannot be remediated, user cannot request exclusion, user is an admin, req has an exclusion.
    @patch.object(scans_table, 'get_latest_complete_scan')
    @patch.object(user_table, 'get_user')
    @patch.object(requirements_table, 'get_item')
    @patch.object(ncr_table, 'query_all')
    def test_get_ncr_single_requirement_id(self, mock_get_ncr, mock_get_requirement, mock_get_user, mock_get_latest_complete_scan):
        mock_get_user.return_value = {
            'email': user,
            'accounts': {},
            'isAdmin': True,
        }
        mock_get_requirement.return_value = {
            'Item': {
                'severity': 'high',
                'description': 'All IAM Users have MFA enabled for Console Access',
                'weight': 1000,
                'source': 's3Import',
                'requirementId': 'requirementId01',
                's3Import':
                {
                    's3Bucket': 's3-req-bucket-01',
                    's3Key': 'req1'
                }
            }
        }
        mock_get_latest_complete_scan.return_value = '2020-05-27T15:11:29.949427#wbnpjzzr'
        mock_get_ncr.return_value = [
            {
                'accountId': '12345678901',
                'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
                'accountName': 'TEST ACCOUNT NAME',
                'scanId': '2020-05-27T15:11:29.949427#wbnpjzzr',
                'accntId_rsrceId_rqrmntId': '12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
                'requirementId': 'requirementId01',
                'rqrmntId_accntId': 'requirementId01_12345678901',
            }
        ]
        event = create_event()
        event['queryStringParameters'] = {
            'requirementId': 'requirementId01'
        }
        resp = ncr.ncr_handler(event, None)
        assert resp['statusCode'] == 200
        assert json.loads(resp['body']) == {
            'scanId': '2020-05-27T15:11:29.949427#wbnpjzzr',
            'ncrRecords': [{
                'ncrId': '2020-05-27T15:11:29.949427#wbnpjzzr#12345678901_arn:aws:lambda:us-west-2:12345678901:function:test-function_requirementId01',
                'allowedActions': {
                    'remediate': False,
                    'requestExclusion': True,
                    'requestExclusionChange': False,
                },
                'resource': {
                    'accountId': '12345678901',
                    'resourceId': 'arn:aws:lambda:us-west-2:12345678901:function:test-function',
                    'accountName': 'TEST ACCOUNT NAME',
                    'requirementId': 'requirementId01',
                }
            }]
        }
