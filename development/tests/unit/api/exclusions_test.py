import json
from unittest.mock import patch, Mock

import pytest

from lib.dynamodb import user_table, exclusions_table, audit_table, requirements_table, scans_table, ncr_table, config_table
from lib.exclusions import exclusions as exclusions_lib
from lib.lambda_decorator import exceptions
from api import exclusions
from tests.unit.api.test_setup_resources import sample_records


EVENT = {
    'queryStringParameters': {},
    'requestContext': {
        'authorizer': {
            'claims': {
                'email': 'test@test.com',
            },
        },
    },
}


class TestGetExclusions:
    @patch.object(exclusions_table, 'scan')
    @patch.object(user_table, 'get_user')
    def test_get_exclusions_admin(self, mock_get_user: Mock, mock_exclusion_scan: Mock):
        mock_get_user.return_value = {
            'isAdmin': True,
        }
        mock_exclusion_scan.return_value = {
            'Items': [{
                'accountId': '123',
                'requirementId': '456',
                'resourceId': '789',
            }],
            'LastEvaluatedKey': None,
        }
        result = exclusions.get_exclusions_handler(EVENT, None)
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['exclusions'][0]['exclusionId'] == '123#456#789'

    @patch.object(user_table, 'get_user')
    def test_get_exclusions_user(self, mock_get_user: Mock):
        mock_get_user.return_value = {
            'isAdmin': False,
        }
        result = exclusions.get_exclusions_handler(EVENT, None)
        assert result['statusCode'] == 403


class TestPutExclusions:
    @patch.object(exclusions, 'update_requires_replacement', Mock(return_value=False))
    @patch.object(user_table, 'get_user', Mock(return_value=sample_records.ADMIN_USER))
    @patch.object(requirements_table, 'get', Mock(return_value={'exclusionType': 'exception'}))
    @patch.object(config_table, 'get_config', Mock(return_value=sample_records.EXCLUSION_TYPES))
    @patch.object(exclusions_table, 'update_exclusion')
    @patch.object(exclusions_lib, 'update_exclusion')
    @patch.object(exclusions, 'get_current_exclusion')
    def test_put_exclusions_admin(self, mock_get_current_exclusion: Mock, mock_update_exclusion: Mock, mock_table_update_exclusion: Mock):
        mock_get_current_exclusion.return_value = sample_records.EXCLUSION_INITIAL
        mock_update_exclusion.return_value = sample_records.EXCLUSION_APPROVED
        event = {
            **EVENT,
            'body': {
                'exclusion': {
                    'status': 'initial',
                    'accountId': '123123123123',
                    'resourceId': 'my-resource',
                    'requirementId': 'My-Requirement',
                },
            },
        }
        result = exclusions.put_exclusions_handler(event, None)
        mock_table_update_exclusion.assert_called()
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['newExclusion']
        assert not body['deleteExclusion']

    @patch.object(exclusions, 'update_requires_replacement', Mock(return_value=True))
    @patch.object(user_table, 'get_user', Mock(return_value=sample_records.ADMIN_USER))
    @patch.object(requirements_table, 'get', Mock(return_value={'exclusionType': 'exception'}))
    @patch.object(config_table, 'get_config', Mock(return_value=sample_records.EXCLUSION_TYPES))
    @patch.object(exclusions_table, 'update_exclusion')
    @patch.object(exclusions_lib, 'update_exclusion')
    @patch.object(exclusions, 'get_current_exclusion')
    def test_put_exclusions_admin_requires_replacement(self, mock_get_current_exclusion: Mock, mock_update_exclusion: Mock, mock_table_update_exclusion: Mock):
        mock_get_current_exclusion.return_value = sample_records.EXCLUSION_INITIAL
        mock_update_exclusion.return_value = sample_records.EXCLUSION_APPROVED
        event = {
            **EVENT,
            'body': {
                'exclusion': {
                    'status': 'initial',
                    'accountId': '123123123123',
                    'resourceId': 'my-resource',
                    'requirementId': 'My-Requirement',
                },
            },
        }
        result = exclusions.put_exclusions_handler(event, None)
        mock_table_update_exclusion.assert_called()
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['newExclusion']
        assert body['newExclusion']['exclusionId']
        assert body['newExclusion']['lastModifiedByAdmin']
        assert body['deleteExclusion']
        assert body['deleteExclusion']['exclusionId']

    @patch.object(user_table, 'get_user')
    def test_put_exclusions_user_throws(self, get_user: Mock):
        get_user.return_value = sample_records.REGULAR_USER
        event = {
            **EVENT,
            'body': {
                'exclusionId': exclusions_table.get_exclusion_id(sample_records.EXCLUSION_INITIAL),
                'exclusion': {
                    'accountId': '*',
                    'status': 'approved',
                },
            },
        }
        result = exclusions.put_exclusions_handler(event, None)
        assert result['statusCode'] == 403


class TestPutExclusionsUser:
    @patch.object(user_table, 'get_user', Mock(return_value=sample_records.ADMIN_USER))
    @patch.object(requirements_table, 'get', Mock(return_value={'exclusionType': 'exception'}))
    @patch.object(config_table, 'get_config', Mock(return_value=sample_records.EXCLUSION_TYPES))
    @patch.object(scans_table, 'get_latest_complete_scan', Mock(return_value='latest-scan-date#randomness'))
    @patch.object(exclusions_lib, 'validate_update_request', Mock())
    @patch.object(audit_table, 'put_audit_trail')
    @patch.object(ncr_table, 'get_ncr')
    @patch.object(exclusions_table, 'update_exclusion')
    def test_put_exclusions_admin(self, table_update_exclusion: Mock, get_ncr: Mock, put_audit: Mock):
        get_ncr.return_value = sample_records.NCR_DATA[0]
        event = {
            **EVENT,
            'body': {
                'ncrId': 'latest-scan-date#randomness#123123123123#my-resource#My-Requirement',
                'exclusion': {
                    'status': 'initial',
                },
            },
        }
        result = exclusions.put_exclusions_for_user_handler(event, None)
        table_update_exclusion.assert_called()
        put_audit.assert_called()
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['newExclusion']

    @patch.object(user_table, 'get_user', Mock(return_value=sample_records.REGULAR_USER))
    @patch.object(requirements_table, 'get', Mock(return_value={'exclusionType': 'exception'}))
    @patch.object(scans_table, 'get_latest_complete_scan', Mock(return_value='latest-scan-date#randomness'))
    @patch.object(config_table, 'get_config', Mock(return_value=sample_records.EXCLUSION_TYPES))
    @patch.object(exclusions_lib, 'validate_update_request', Mock())
    @patch.object(audit_table, 'put_audit_trail')
    @patch.object(ncr_table, 'get_ncr')
    @patch.object(exclusions_table, 'update_exclusion')
    def test_put_exclusions_user(self, table_update_exclusion: Mock, get_ncr: Mock, put_audit: Mock):
        get_ncr.return_value = sample_records.NCR_DATA[0]
        event = {
            **EVENT,
            'body': {
                'ncrId': 'latest-scan-date#randomness#123123123123#my-resource#My-Requirement',
                'exclusion': {
                    'status': 'approved',
                },
            },
        }
        result = exclusions.put_exclusions_for_user_handler(event, None)
        table_update_exclusion.assert_called()
        put_audit.assert_called()
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['newExclusion']

    @patch.object(user_table, 'get_user')
    def test_put_exclusions_user_no_update(self, get_user: Mock):
        get_user.return_value = sample_records.REGULAR_USER
        event = {
            **EVENT,
            'body': {
                'exclusionId': exclusions_table.get_exclusion_id(sample_records.EXCLUSION_INITIAL),
            },
        }
        result = exclusions.put_exclusions_for_user_handler(event, None)
        assert result['statusCode'] == 400


class TestGetCurrentExclusion:
    @patch.object(exclusions_table, 'get_exclusion')
    def test_get_current_exclusion(self, mock_get_exclusion):
        mock_get_exclusion.return_value = {'current': 'exclusion'}
        result = exclusions.get_current_exclusion({'exclusionId': 'sampletext'})
        assert result == mock_get_exclusion.return_value

    @patch.object(exclusions_table, 'get_exclusion')
    def test_get_current_exclusion_not_found(self, mock_get_exclusion):
        mock_get_exclusion.return_value = None
        with pytest.raises(exceptions.HttpNotFoundException):
            exclusions.get_current_exclusion({'exclusionId': 'sampletext'})

    @patch.object(exclusions_table, 'get_exclusion')
    def test_get_current_exclusion_no_exclusion_id(self, mock_get_exclusion):
        mock_get_exclusion.return_value = None
        result = exclusions.get_current_exclusion({})
        assert result == {}


class TestUpdateRequiresReplacement:
    def test_update_requires_placement(self):
        result = exclusions.update_requires_replacement({
            'status': 'initial',
            'accountId': 'abc',
            'requirementId': '123',
            'resourceId': 'def',
        }, {
            'status': 'approved',
            'accountId': 'ghi',
        })
        assert result is True

    def test_update_requires_placement_update_request_same(self):
        result = exclusions.update_requires_replacement({
            'status': 'initial',
            'accountId': 'abc',
            'requirementId': '123',
            'resourceId': 'def',
        }, {
            'status': 'approved',
            'accountId': 'abc',
            'requirementId': '123',
            'resourceId': 'def',
        })
        assert result is False

    def test_update_requires_placement_update_no_current_exclusion(self):
        result = exclusions.update_requires_replacement({}, {
            'status': 'approved',
            'accountId': 'abc',
            'requirementId': '123',
            'resourceId': 'def',
        })
        assert result is False
