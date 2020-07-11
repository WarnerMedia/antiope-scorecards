import json
from datetime import datetime
from lib.logger import logger
from lib.lambda_decorator import exceptions
from lib.exclusions import state_machine
from lib.dict_merge import dict_merge

START = state_machine.States.start
INITIAL = state_machine.States.initial
APPROVED = state_machine.States.approved
APPROVED_PENDING_CHANGES = state_machine.States.approved_pending_changes
REJECTED = state_machine.States.rejected
ARCHIVED = state_machine.States.archived

REQUEST_EXCLUSION_STATES = [INITIAL]
REQUEST_EXCLUSION_CHANGE_STATES = [APPROVED_PENDING_CHANGES]


def is_wildcard_exclusion(exclusion: dict) -> bool:
    if '*' in exclusion.get('accountId', ''):
        return True
    if '*' in exclusion.get('resourceId', ''):
        return True
    return False


def get_state(exclusion: dict):
    """
    Get the state of the given exclusion (valid states in state_machine module)
    """
    if exclusion.get('updateRequested') and exclusion.get('status') != 'approved':
        raise exceptions.HttpInvalidException('Invalid state, cannot have updateRequested if status is not approved')
    if 'status' not in exclusion:
        return 'start'
    if exclusion['status'] not in [START, INITIAL, APPROVED, REJECTED, ARCHIVED]:
        raise exceptions.HttpInvalidException(f'Exclusion status invalid: {exclusion["status"]}')
    if exclusion['status'] == APPROVED:
        return APPROVED_PENDING_CHANGES if exclusion.get('updateRequested') else APPROVED
    return exclusion['status']


def validate_update_request(old_exclusion: dict, update_request: dict, machine: dict, exclusion_config: dict, is_admin: bool):
    """
    Validate the exclusions put request.
        - state change is valid
        - necessary permissions are present
        - referenced resources exist
    """
    prospective_exclusion = dict_merge(old_exclusion, update_request)
    old_state = get_state(old_exclusion)
    new_state = get_state(prospective_exclusion)
    schema = state_machine.get_state_transition(machine, old_state, new_state)
    if not schema:
        raise exceptions.HttpInvalidExclusionStateChange(old_exclusion, update_request, {'message': f'cannot go from {old_state} to {new_state}'})

    required_keys = [key for key, (required, validator) in schema.items() if required]
    missing_keys = [required_key for required_key in required_keys if required_key not in update_request]
    extra_keys = [request_key for request_key in update_request if request_key not in schema]
    if missing_keys or extra_keys:
        raise exceptions.HttpInvalidExclusionStateChange(old_exclusion, update_request, {
            'missingKeys': missing_keys,
            'extraKeys': extra_keys,
        })

    validation_errors = []
    for key, (_, validator) in schema.items():
        if key not in update_request:
            continue
        if callable(validator):
            is_valid, message = validator(old_exclusion, update_request, exclusion_config, is_admin)
            if not is_valid:
                validation_errors.append({
                    'property': key,
                    'message': message,
                })
    if validation_errors:
        raise exceptions.HttpInvalidExclusionStateChange(old_exclusion, update_request, {
            'validationErrors': validation_errors,
        })


def update_exclusion(old_exclusion: dict, update_request: dict, exclusion_config: dict, is_admin: bool) -> dict:
    """
    Validate and apply the exclusion update.
    Return the updated exclusion to be saved in the database.
    """
    if not update_request:
        raise exceptions.HttpInvalidException('Must supply exclusion in the body')
    machine = state_machine.ADMIN_STATE_TRANSITIONS if is_admin else state_machine.USER_STATE_TRANSITIONS
    validate_update_request(old_exclusion, update_request, machine, exclusion_config, is_admin)

    new_exclusion = dict_merge(old_exclusion, update_request)
    if old_exclusion.get('status') != new_exclusion['status']:
        new_exclusion['lastStatusChangeDate'] = datetime.now().isoformat()

    logger.debug('Updated exclusion: %s', json.dumps(new_exclusion))
    return new_exclusion
