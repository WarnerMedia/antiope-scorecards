from unittest.mock import patch, Mock

import pytest

from lib.lambda_decorator import exceptions
from lib.exclusions import exclusions, state_machine
from tests.unit.api.test_setup_resources import sample_records


EXCEPTION = sample_records.EXCLUSION_TYPES['exception']


def PASS(*args): # pylint: disable=invalid-name
    return True, None


def FAIL(*args): # pylint: disable=invalid-name
    return False, 'fail'


class TestGetState:
    def test_invalid(self):
        with pytest.raises(exceptions.HttpInvalidException):
            exclusions.get_state({'status': 'somethingbad'})

    def test_start(self):
        state = exclusions.get_state({})
        assert state == state_machine.States.start

    def test_initial(self):
        state = exclusions.get_state(sample_records.EXCLUSION_INITIAL)
        assert state == state_machine.States.initial

    def test_approved(self):
        state = exclusions.get_state(sample_records.EXCLUSION_APPROVED)
        assert state == state_machine.States.approved

    def test_approved_pending_changes(self):
        state = exclusions.get_state(sample_records.EXCLUSION_APPROVED_PENDING_CHANGES)
        assert state == state_machine.States.approved_pending_changes

    def test_rejected(self):
        state = exclusions.get_state(sample_records.EXCLUSION_REJECTED)
        assert state == state_machine.States.rejected

    def test_archived(self):
        state = exclusions.get_state(sample_records.EXCLUSION_ARCHIVED)
        assert state == state_machine.States.archived


class TestValidateUpdateRequestGeneral:
    @patch.object(state_machine, 'get_state_transition', Mock(return_value={}))
    @patch.object(exclusions, 'get_state')
    def test_invalid_status_change(self, get_state):
        with pytest.raises(exceptions.HttpInvalidExclusionStateChange):
            exclusions.validate_update_request({}, {}, state_machine.ADMIN_STATE_TRANSITIONS, EXCEPTION, True)

    @patch.object(state_machine, 'get_state_transition', Mock(return_value={'status': (True, True)}))
    @patch.object(exclusions, 'get_state')
    def test_invalid_keys(self, get_state):
        with pytest.raises(exceptions.HttpInvalidExclusionStateChange) as excinfo:
            exclusions.validate_update_request({}, {'extra': 'key'}, state_machine.ADMIN_STATE_TRANSITIONS, EXCEPTION, True)
        assert excinfo.value.body['body']['errors']['missingKeys'] == [
            'status',
        ]
        assert excinfo.value.body['body']['errors']['extraKeys'] == [
            'extra',
        ]

    @patch.object(state_machine, 'get_state_transition')
    @patch.object(exclusions, 'get_state', Mock())
    def test_fail(self, get_state_transition: Mock):
        get_state_transition.return_value = {
            'status': (True, lambda *args: (False, 'bad'))
        }
        with pytest.raises(exceptions.HttpInvalidExclusionStateChange) as excinfo:
            exclusions.validate_update_request({}, {'status': 'something'}, state_machine.ADMIN_STATE_TRANSITIONS, EXCEPTION, False)
        invalid_properties = [error['property'] for error in excinfo.value.body['body']['errors']['validationErrors']]
        assert invalid_properties == ['status']


class TestUpdateExclusion:
    @patch.object(exclusions, 'validate_update_request')
    def test_update_exclusion(self, mock_validate_update_request: Mock):
        new_exclusion = exclusions.update_exclusion(sample_records.EXCLUSION_INITIAL, {
            'status': 'approved',
            'formFields': {
                'reason': 'new reason',
            },
            'adminComments': 'my comment'
        }, EXCEPTION, True)
        mock_validate_update_request.assert_called()
        assert new_exclusion['formFields']['reason'] == 'new reason'
        assert new_exclusion['status'] == 'approved'
        assert new_exclusion['adminComments'] == 'my comment'
        assert 'lastStatusChangeDate' in new_exclusion
        assert new_exclusion['lastStatusChangeDate'] != sample_records.EXCLUSION_INITIAL['lastStatusChangeDate']

    def test_update_exclusion_missing_update_request(self):
        with pytest.raises(exceptions.HttpInvalidException):
            exclusions.update_exclusion(sample_records.EXCLUSION_INITIAL, {}, EXCEPTION, True)
