from unittest.mock import Mock, patch

from lib import ncr_util, authz
from tests.unit.api.test_setup_resources import sample_records


class TestGetAllowedActions:
    @patch.object(authz, 'can_request_exclusion', Mock(return_value=(True, None)))
    @patch.object(authz, 'can_remediate', Mock(return_value=(False, None)))
    def test_request_exclusion_true(self):
        result = ncr_util.get_allowed_actions(sample_records.REGULAR_USER, '123123123123', {}, {})
        assert result['requestExclusion']

    @patch.object(authz, 'can_request_exclusion', Mock(return_value=(False, None)))
    @patch.object(authz, 'can_remediate', Mock(return_value=(False, None)))
    def test_request_exclusion_false_permissions(self):
        result = ncr_util.get_allowed_actions(sample_records.REGULAR_USER, '123123123123', {}, {})
        assert not result['requestExclusion']

    @patch.object(authz, 'can_request_exclusion', Mock(return_value=(True, None)))
    @patch.object(authz, 'can_remediate', Mock(return_value=(False, None)))
    def test_request_exclusion_false_state(self):
        result = ncr_util.get_allowed_actions(sample_records.REGULAR_USER, '123123123123', {}, {'status': 'approved'})
        assert not result['requestExclusion']

    @patch.object(authz, 'can_request_exclusion', Mock(return_value=(True, None)))
    @patch.object(authz, 'can_remediate', Mock(return_value=(False, None)))
    def test_request_exclusion_change_true(self):
        result = ncr_util.get_allowed_actions(sample_records.REGULAR_USER, '123123123123', {}, {'status': 'approved'})
        assert result['requestExclusionChange']

    @patch.object(authz, 'can_request_exclusion', Mock(return_value=(False, None)))
    @patch.object(authz, 'can_remediate', Mock(return_value=(False, None)))
    def test_request_exclusion_change_false_permissions(self):
        result = ncr_util.get_allowed_actions(sample_records.REGULAR_USER, '123123123123', {}, {})
        assert not result['requestExclusionChange']

    @patch.object(authz, 'can_request_exclusion', Mock(return_value=(False, None)))
    @patch.object(authz, 'can_remediate', Mock(return_value=(False, None)))
    def test_request_exclusion_change_false_state(self):
        result = ncr_util.get_allowed_actions(sample_records.REGULAR_USER, '123123123123', {}, {})
        assert result == {
            'remediate': False,
            'requestExclusion': False,
            'requestExclusionChange': False,
        }

    @patch.object(authz, 'can_request_exclusion', Mock(return_value=(False, None)))
    @patch.object(authz, 'can_remediate', Mock(return_value=(True, None)))
    def test_remediate_true(self):
        result = ncr_util.get_allowed_actions(sample_records.REGULAR_USER, '123123123123', {'remediation': True}, {})
        assert result == {
            'remediate': True,
            'requestExclusion': False,
            'requestExclusionChange': False,
        }

    @patch.object(authz, 'can_request_exclusion', Mock(return_value=(False, None)))
    @patch.object(authz, 'can_remediate', Mock(return_value=(False, None)))
    def test_remediate_false_permissions(self):
        result = ncr_util.get_allowed_actions(sample_records.REGULAR_USER, '123123123123', {'remediation': True}, {})
        assert result == {
            'remediate': False,
            'requestExclusion': False,
            'requestExclusionChange': False,
        }

    @patch.object(authz, 'can_request_exclusion', Mock(return_value=(False, None)))
    @patch.object(authz, 'can_remediate', Mock(return_value=(True, None)))
    def test_remediate_false_requirement(self):
        result = ncr_util.get_allowed_actions(sample_records.REGULAR_USER, '123123123123', {}, {})
        assert result == {
            'remediate': False,
            'requestExclusion': False,
            'requestExclusionChange': False,
        }
