import json

from lib import authz
from lib.logger import logger
from lib.exclusions import exclusions, state_machine


def get_allowed_actions(user, account_id, requirement, exclusion):
    allowed_actions = {
        'remediate': False,
        'requestExclusion': False,
        'requestExclusionChange': False,
    }
    current_state = exclusions.get_state(exclusion)
    valid_state_transitions = state_machine.USER_STATE_TRANSITIONS.get(current_state, {}).keys()
    logger.debug('Current state: %s', current_state)
    logger.debug('Valid state transitions: %s', str(valid_state_transitions))
    logger.debug('User: %s', json.dumps(user))

    if authz.can_request_exclusion(user, account_id)[0]:
        if set(valid_state_transitions) & set(exclusions.REQUEST_EXCLUSION_STATES):
            allowed_actions['requestExclusion'] = True
        if set(valid_state_transitions) & set(exclusions.REQUEST_EXCLUSION_CHANGE_STATES):
            allowed_actions['requestExclusionChange'] = True

    # Determine If can remediate
    if can_requirement_be_remediated(requirement):
        allowed_actions['remediate'] = authz.can_remediate(user, account_id)[0]
    return allowed_actions


def can_requirement_be_remediated(requirement):
    """
    Mehtod to validate whether a requirement is capable of being remediated.

    :param requirement: The dict representing the requirement to check.

    :returns bool: A boolean representing whether requirement can or cannot be remediated.
    """
    return 'remediation' in requirement
