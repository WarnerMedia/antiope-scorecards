import io
import os
import json
from datetime import datetime
from unittest import TestCase
from unittest.mock import patch

from botocore.stub import Stubber, ANY
import pytest

from api import remediate
from lib.dynamodb import user_table
from remediation.workers.worker_base import RemediationStatus


class TestRemediateInvokeWorker():
    def test_invoke_worker_lambda_error(self, lambda_stubber: Stubber):
        lambda_stubber.add_client_error(
            'invoke', 'ResourceNotFoundException', '', 404,
            expected_params={'FunctionName': 'worker', 'Payload': ANY}
        )
        status, message = remediate.invoke_worker('worker', {})
        lambda_stubber.assert_no_pending_responses()

        assert status == RemediationStatus.ERROR
        assert message == 'Error invoking remediation worker'

    def test_invoke_worker_error(self, lambda_stubber: Stubber):
        lambda_stubber.add_response(
            'invoke', {
                'FunctionError': 'Unhandled', 'Payload': io.StringIO('{"error": "TypeError"}')
            },
        )
        status, message = remediate.invoke_worker('worker', {})
        lambda_stubber.assert_no_pending_responses()

        assert status == RemediationStatus.ERROR
        assert message == '{"error": "TypeError"}'

    def test_invoke_worker_reported_error(self, lambda_stubber: Stubber):
        lambda_stubber.add_response(
            'invoke', {
                'Payload': io.StringIO('{"status": "error", "message":"error happened"}')
            },
        )
        status, message = remediate.invoke_worker('worker', {})
        lambda_stubber.assert_no_pending_responses()

        assert status == RemediationStatus.ERROR
        assert message == 'error happened'

    def test_invoke_worker_malformed_response(self, lambda_stubber: Stubber):
        lambda_stubber.add_response(
            'invoke', {
                'Payload': io.StringIO('{"status_x": "error", "message":"error happened"}')
            },
        )
        status, message = remediate.invoke_worker('worker', {})
        lambda_stubber.assert_no_pending_responses()

        assert status == RemediationStatus.ERROR
        assert message == 'Invalid response from remediation'

    def test_invoke_worker_invalid_status(self, lambda_stubber: Stubber):
        lambda_stubber.add_response(
            'invoke', {
                'Payload': io.StringIO('{"status": "invalid_status", "message":"error happened"}')
            },
        )
        status, message = remediate.invoke_worker('worker', {})
        lambda_stubber.assert_no_pending_responses()

        assert status == RemediationStatus.ERROR
        assert message == 'Invalid status code response from remediation'

    def test_invoke_worker_valid_response(self, lambda_stubber: Stubber):
        lambda_stubber.add_response(
            'invoke', {
                'Payload': io.StringIO('{"status": "iacOverrideRequired", "message":"iac override required"}')
            },
        )
        status, message = remediate.invoke_worker('worker', {})
        lambda_stubber.assert_no_pending_responses()

        assert status == 'iacOverrideRequired'
        assert message == 'iac override required'

    def test_invoke_worker_invalid_json(self, lambda_stubber: Stubber):
        lambda_stubber.add_response(
            'invoke', {
                'Payload': io.StringIO('{"status: "invalid_status", "message":"error happened"}')
            },
        )
        status, message = remediate.invoke_worker('worker', {})
        lambda_stubber.assert_no_pending_responses()

        assert status == RemediationStatus.ERROR
        assert message == 'Invalid JSON response from remediation'


@pytest.fixture(scope='function')
def lambda_stubber():
    with Stubber(remediate.lambda_client) as lambda_stubber:
        yield lambda_stubber


@pytest.fixture(scope='function')
def sts_stubber():
    with Stubber(remediate.boto_sts) as sts_stubber:
        yield sts_stubber


@pytest.fixture(scope='function')
def sns_stubber():
    with Stubber(remediate.sns_client) as sns_stubber:
        yield sns_stubber


@pytest.fixture(scope='function')
def audit_stubber():
    with Stubber(remediate.audit_table.table.meta.client) as audit_stubber:
        yield audit_stubber


@pytest.fixture(scope='function')
def ncr_stubber():
    with Stubber(remediate.ncr_table.table.meta.client) as ncr_stubber:
        yield ncr_stubber


@pytest.fixture(scope='function')
def account_stubber():
    with Stubber(remediate.accounts_table.table.meta.client) as account_stubber:
        yield account_stubber


@pytest.fixture(scope='function')
def requirement_stubber():
    with Stubber(remediate.requirements_table.table.meta.client) as requirement_stubber:
        yield requirement_stubber


@pytest.fixture(scope='function')
def user_stubber():
    with Stubber(user_table.table.meta.client) as user_stubber:
        yield user_stubber


@pytest.fixture(scope='function')
def config_stubber():
    with Stubber(remediate.config_table.table.meta.client) as config_stubber:
        yield config_stubber


class TestCheckNcr(TestCase):
    @patch.object(remediate.ncr_table, 'get_item')
    def test_check_ncr_found(self, mock_ncr_get_item):
        item = {
            'scanId': '16-06-2020#coaecuoja',
            'accntId_rsrceId_rqrmntId': '338938933893#resource-identifier-sample#293929'
        }
        mock_ncr_get_item.return_value = {
            'Item': item
        }
        result = remediate.check_ncr(item['scanId'] + '#' + item['accntId_rsrceId_rqrmntId'])
        assert result == item

    @patch.object(remediate.ncr_table, 'get_item')
    def test_check_ncr_not_found(self, mock_ncr_get_item):
        item = {
            'scanId': '16-06-2020#coaecuoja',
            'accntId_rsrceId_rqrmntId': '338938933893#resource-identifier-sample#293929'
        }
        mock_ncr_get_item.side_effect = (
            lambda **kwargs: {'Item': item} if kwargs['Key']['scanId'] == item['scanId'] else {}
        )
        incorrect_scan_id = '11-11-2011#rcdoe'
        with self.assertRaises(remediate.HttpNotFoundException):
            remediate.check_ncr(incorrect_scan_id + '#' + item['accntId_rsrceId_rqrmntId'])


class TestGetRolesArns(TestCase):
    @patch.object(remediate.accounts_table, 'get_item')
    def test_get_roles_arns_found(self, mock_account_get_item):
        account_id = '111'
        item = {
            'cross_account_role': f'arn:aws:iam::{account_id}:role/cross-account'
        }
        mock_account_get_item.return_value = {
            'Item': item
        }
        os.putenv('REMEDIATION_ROLE_NAME', 'sample_value')
        result_read_only, result_remediation = remediate.get_roles_arns(account_id)
        assert result_read_only == item['cross_account_role']
        assert result_remediation == f'arn:aws:iam::{account_id}:role/{os.getenv("REMEDIATION_ROLE_NAME")}'

    @patch.object(remediate.accounts_table, 'get_item')
    def test_get_roles_arns_not_found(self, mock_account_get_item):
        account_id = '111'
        item = {
            'cross_account_role': f'arn:aws:iam::{111}:role/cross-account'
        }
        mock_account_get_item.side_effect = (
            lambda **kwargs: {'Item': item} if kwargs['Key']['accountId'] == account_id else {}
        )
        incorrect_account_id = '222'
        os.putenv('REMEDIATION_ROLE_NAME', 'sample_value')
        with self.assertRaises(remediate.HttpNotFoundException):
            remediate.get_roles_arns(incorrect_account_id)


class TestValidateInput(TestCase):
    def test_validate_input_valid(self):
        remediation = {
            'parameters': {
                'key_1': 'value_1',
                'key_2': 'value_2',
                'key_3': 'value_3'
            }
        }
        given_params = {
            'key_1': 'sample_1',
            'key_2': 'sample_2',
            'key_3': 'sample_3'
        }
        assert remediate.validate_input(given_params, remediation) is None

    def test_validate_input_not_valid(self):
        remediation = {
            'parameters': {
                'key_1': 'value_1',
                'key_2': 'value_2',
                'key_3': 'value_3'
            }
        }
        given_params = {
            'bad_key_1': 'sample_1',
            'bad_key_2': 'sample_2',
            'bad_key_3': 'sample_3'
        }
        with self.assertRaises(remediate.HttpInvalidException):
            remediate.validate_input(given_params, remediation)

    def test_validate_input_not_dict(self):
        remediation = {
            'parameters': {
                'key_1': 'value_1',
                'key_2': 'value_2',
                'key_3': 'value_3'
            }
        }
        given_params = ('key_1', 'key_2', 'key_3')
        with self.assertRaises(remediate.HttpInvalidException):
            remediate.validate_input(given_params, remediation)


class TestHasRemediationRoles:
    def test_has_roles(self, sts_stubber: Stubber):
        sts_stubber.add_response(
            'assume_role',
            {
                'Credentials': {'SecretAccessKey': 'Foo', 'SessionToken': 'Bar', 'Expiration': datetime.now(),
                                'AccessKeyId': 'jduiidjujiduidjuidjuidjiduj'}
            }
        )
        sts_stubber.add_response(
            'assume_role',
            {
                'Credentials': {'SecretAccessKey': 'Foo', 'SessionToken': 'Bar', 'Expiration': datetime.now(),
                                'AccessKeyId': 'jduiidjujiduidjuidjuidjiduj'}
            }
        )
        result = remediate.has_remediation_roles(
            'sample@sample.com',
            'arn:aws:iam::111:role/cross-account',
            'arn:aws:iam::111:role/remediation-role'
        )
        assert result == (True, None)

    def test_not_has_read_only(self, sts_stubber: Stubber):
        sts_stubber.add_client_error('assume_role')
        sts_stubber.add_response(
            'assume_role',
            {
                'Credentials': {'SecretAccessKey': 'Foo', 'SessionToken': 'Bar', 'Expiration': datetime.now(),
                                'AccessKeyId': 'jduiidjujiduidjuidjuidjiduj'}
            }
        )
        result = remediate.has_remediation_roles(
            'sample@sample.com',
            'arn:aws:iam::111:role/cross-account',
            'arn:aws:iam::111:role/remediation-role'
        )
        sts_stubber.assert_no_pending_responses()

        assert result[0] is False


class TestRequireRemediationRoles:
    def test_has_roles(self, sts_stubber: Stubber):
        sts_stubber.add_response(
            'assume_role',
            {
                'Credentials': {'SecretAccessKey': 'Foo', 'SessionToken': 'Bar', 'Expiration': datetime.now(),
                                'AccessKeyId': 'jduiidjujiduidjuidjuidjiduj'}
            }
        )
        sts_stubber.add_response(
            'assume_role',
            {
                'Credentials': {'SecretAccessKey': 'Foo', 'SessionToken': 'Bar', 'Expiration': datetime.now(),
                                'AccessKeyId': 'jduiidjujiduidjuidjuidjiduj'}
            }
        )
        assert remediate.require_remediation_roles(
            'sample@sample.com',
            'arn:aws:iam::111:role/cross-account',
            'arn:aws:iam::111:role/remediation-role'
        ) is None
        sts_stubber.assert_no_pending_responses()

    def test_not_has_roles(self, sts_stubber: Stubber):
        sts_stubber.add_client_error('assume_role')
        sts_stubber.add_client_error('assume_role')
        with pytest.raises(remediate.HttpInvalidException):
            remediate.require_remediation_roles(
                'sample@sample.com',
                'arn:aws:iam::111:role/cross-account',
                'arn:aws:iam::111:role/remediation-role'
            )


class TestRemediateManagerHandler:
    def test_all_checks_passing(
            self, sts_stubber: Stubber, lambda_stubber: Stubber, sns_stubber: Stubber,
            audit_stubber: Stubber, ncr_stubber: Stubber, account_stubber: Stubber,
            requirement_stubber: Stubber, user_stubber: Stubber, config_stubber: Stubber
    ):
        sts_stubber.add_response(
            'assume_role',
            {
                'Credentials': {'SecretAccessKey': 'Foo', 'SessionToken': 'Bar', 'Expiration': datetime.now(),
                                'AccessKeyId': 'jduiidjujiduidjuidjuidjiduj'}
            }
        )
        sts_stubber.add_response(
            'assume_role',
            {
                'Credentials': {'SecretAccessKey': 'Foo', 'SessionToken': 'Bar', 'Expiration': datetime.now(),
                                'AccessKeyId': 'jduiidjujiduidjuidjuidjiduj'}
            }
        )
        user_stubber.add_response(
            'get_item',
            {'Item': {
                'email': {'S': 'sample@sample.com'},
                'isAdmin': {'BOOL': False},
                'accounts': {'M': {
                    '465456456456456456456': {'M': {
                        'permissions': {'M': {
                            'triggerRemediation': {'BOOL': True}}}}}}}}})
        ncr_stubber.add_response(
            'get_item',
            {
                'Item': {
                    'accntId_rsrceId_rqrmntId': {
                        'S': '465456456456456456456#arn:aws:ec2:us-east-2:465456456456456456456:security-group/sg-oeuaaoeuaoeuaoeuoau#All-Open_Ports'},
                    'scanId': {'S': '16-06-2020#coaecuoja'},
                    'accountId': {'S': '465456456456456456456'},
                    'accountName': {'S': 'aws-aaa-sandbox'},
                    'reason': {
                        'S': 'Security group: sg-oeuaaoeuaoeuaoeuoau (foo) has all ports open to 0.0.0.0/0 and all ports open to ::/0'},
                    'region': {'S': 'us-east-2'},
                    'requirementId': {'S': 'All-Open_Ports'},
                    'resourceId': {
                        'S': 'arn:aws:ec2:us-east-2:465456456456456456456:security-group/sg-oeuaaoeuaoeuaoeuoau'},
                    'resourceType': {'S': 'EC2'}
                }
            })
        ncr_stubber.add_response(
            'update_item',
            {
                'Attributes': {
                    'accntId_rsrceId_rqrmntId': {
                        'S': '465456456456456456456#arn:aws:ec2:us-east-2:465456456456456456456:security-group/sg-oeuaaoeuaoeuaoeuoau#All-Open_Ports'},
                    'scanId': {'S': '16-06-2020#coaecuoja'},
                    'accountId': {'S': '465456456456456456456'},
                    'accountName': {'S': 'aws-aaa-sandbox'},
                    'reason': {
                        'S': 'Security group: sg-oeuaaoeuaoeuaoeuoau (foo) has all ports open to 0.0.0.0/0 and all ports open to ::/0'},
                    'region': {'S': 'us-east-2'},
                    'requirementId': {'S': 'All-Open_Ports'},
                    'resourceId': {
                        'S': 'arn:aws:ec2:us-east-2:465456456456456456456:security-group/sg-oeuaaoeuaoeuaoeuoau'},
                    'resourceType': {'S': 'EC2'},
                    'remediated': {'S': remediate.ncr_table.REMEDIATION_SUCCESS}
                }
            })
        ncr_stubber.add_response(
            'update_item',
            {
                'Attributes': {
                    'accntId_rsrceId_rqrmntId': {
                        'S': '465456456456456456456#arn:aws:ec2:us-east-2:465456456456456456456:security-group/sg-oeuaaoeuaoeuaoeuoau#All-Open_Ports'},
                    'scanId': {'S': '16-06-2020#coaecuoja'},
                    'accountId': {'S': '465456456456456456456'},
                    'accountName': {'S': 'aws-aaa-sandbox'},
                    'reason': {
                        'S': 'Security group: sg-oeuaaoeuaoeuaoeuoau (foo) has all ports open to 0.0.0.0/0 and all ports open to ::/0'},
                    'region': {'S': 'us-east-2'},
                    'requirementId': {'S': 'All-Open_Ports'},
                    'resourceId': {
                        'S': 'arn:aws:ec2:us-east-2:465456456456456456456:security-group/sg-oeuaaoeuaoeuaoeuoau'},
                    'resourceType': {'S': 'EC2'},
                    'remediated': {'S': remediate.ncr_table.REMEDIATION_SUCCESS}
                }
            })
        audit_stubber.add_response(
            'put_item',
            {
                'Attributes': {
                    'remediated': {'S': remediate.ncr_table.REMEDIATION_IN_PROGRESS}
                }
            }
        )
        audit_stubber.add_response(
            'put_item',
            {
                'Attributes': {
                    'remediated': {'S': remediate.ncr_table.REMEDIATION_SUCCESS}
                }
            }
        )
        requirement_stubber.add_response(
            'get_item',
            {
                'Item': {
                    'remediation': {'M': {
                        'remediationId': {'S': 'bbb'}
                    }}
                }
            }
        )
        account_stubber.add_response(
            'get_item',
            {
                'Item': {
                    'cross_account_role': {'S': 'arn:aws:iam::465456456456456456456:role/sample-text'}
                }
            }
        )
        config_stubber.add_response(
            'get_item',
            {
                'Item': {
                    'config': {'M': {
                        'bbb': {'M': {
                            'parameters': {'M': {
                                'CIDR': {'S': 'foo'}
                            }},
                            'lambdaFunctionName': {'S': 'bizbaz'}
                        }}
                    }}
                }
            }
        )
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'email': 'sample@sample.com'
                    }
                }
            },
            'body': json.dumps({
                'ncrId': '2020-06-05T20:02:37.770740#ghywlgtr#055850966408#arn:aws:ec2:us-east-2'
                         ':465456456456456456456:security-group/sg-oeuaaoeuaoeuaoeuoau#All-Open_Ports',
                'remediationParameters': {
                    'CIDR': '10.0.0.2/24'
                },
                'overrideIacWarning': True,
                'read_only_role_arn': 'arn:aws:iam::465456456456456456456:role/sample-text',
                'role_session_name': 'bar',
                'remediation_arn': 'arn:aws:iam::465456456456456456456:role/remediation-role'
            })
        }
        lambda_stubber.add_response(
            'invoke', {
                'Payload': io.StringIO('{"status": "success", "message":"ok"}')
            },
        )
        results = remediate.remediate_manager_handler(event,
                                                      {})
        print(results)
        assert json.loads(results['body']) == {
            'status': 'success',
            'message': 'ok',
            'updatedNcr': {
                'accntId_rsrceId_rqrmntId': '465456456456456456456#arn:aws:ec2:us-east-2:465456456456456456456'
                                            ':security-group/sg-oeuaaoeuaoeuaoeuoau#All-Open_Ports',
                'scanId': '16-06-2020#coaecuoja',
                'accountId': '465456456456456456456',
                'accountName': 'aws-aaa-sandbox',
                'reason': 'Security group: sg-oeuaaoeuaoeuaoeuoau (foo) has all ports open to 0.0.0.0/0 and all ports open to ::/0',
                'region': 'us-east-2',
                'requirementId': 'All-Open_Ports',
                'resourceId': 'arn:aws:ec2:us-east-2:465456456456456456456:security-group/sg-oeuaaoeuaoeuaoeuoau',
                'resourceType': 'EC2',
                'remediated': remediate.ncr_table.REMEDIATION_SUCCESS
            }
        }
        assert results['statusCode'] == 200
