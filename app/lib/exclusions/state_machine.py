from lib.exclusions import validators

class States:
    start = 'start'
    initial = 'initial'
    approved = 'approved'
    approved_pending_changes = 'approvedPendingChanges'
    rejected = 'rejected'
    archived = 'archived'

USER_CREATE = {
    'status': (True, None),
    'expirationDate': (True, validators.expiration_date),
    'formFields': (True, validators.form_fields),
}
USER_UPDATE = {
    'status': (True, None),
    'expirationDate': (False, validators.expiration_date),
    'formFields': (False, validators.form_fields),
}
USER_REQUEST_CHANGES = {
    'status': (False, True),
    'updateRequested': (True, validators.update_requested),
}

USER_STATE_TRANSITIONS = {
    States.start: {
        States.initial: USER_CREATE,
    },
    States.initial: {
        States.initial: USER_UPDATE,
    },
    States.approved: {
        States.approved_pending_changes: USER_REQUEST_CHANGES,
    },
    States.approved_pending_changes: {
        States.approved_pending_changes: USER_REQUEST_CHANGES,
    },
    States.rejected: {
        States.initial: USER_UPDATE,
    },
    States.archived: {
        States.initial: USER_UPDATE,
    },
}

ADMIN_CREATE = {
    'status': (True, None),
    'accountId': (True, validators.account_id),
    'resourceId': (True, validators.resource_id),
    'requirementId': (True, validators.requirement_id),
    'expirationDate': (True, validators.expiration_date),
    'formFields': (True, validators.form_fields),
    'adminComments': (False, validators.admin_comments),
    'hidesResources': (False, validators.hides_resources),
}
ADMIN_UPDATE = {
    'status': (True, None),
    'accountId': (False, validators.account_id),
    'resourceId': (False, validators.resource_id),
    'expirationDate': (False, validators.expiration_date),
    'formFields': (False, validators.form_fields),
    'adminComments': (False, validators.admin_comments),
    'hidesResources': (False, validators.hides_resources),
}
ADMIN_REQUEST_CHANGES = {
    'status': (False, True),
    'accountId': (False, validators.account_id),
    'resourceId': (False, validators.resource_id),
    'expirationDate': (False, validators.expiration_date),
    'formFields': (False, validators.form_fields),
    'adminComments': (False, validators.admin_comments),
    'hidesResources': (False, validators.hides_resources),
    'updateRequested': (True, validators.update_requested),
}
ADMIN_APPROVE_CHANGES = {
    'updateRequested': (True, validators.update_requested),
    'status': (False, None),
    'expirationDate': (False, validators.expiration_date),
    'formFields': (False, validators.form_fields),
    'adminComments': (False, validators.admin_comments),
    'hidesResources': (False, validators.hides_resources),
}

ADMIN_STATE_TRANSITIONS = {
    States.start: {
        States.initial: ADMIN_CREATE,
    },
    States.initial: {
        States.initial: ADMIN_UPDATE,
        States.approved: ADMIN_UPDATE,
        States.rejected: ADMIN_UPDATE,
        States.archived: ADMIN_UPDATE,
    },
    States.approved: {
        States.initial: ADMIN_UPDATE,
        States.approved: ADMIN_UPDATE,
        States.rejected: ADMIN_UPDATE,
        States.archived: ADMIN_UPDATE,
    },
    States.approved_pending_changes: {
        States.initial: ADMIN_UPDATE,
        States.approved: ADMIN_APPROVE_CHANGES,
        States.approved_pending_changes: ADMIN_REQUEST_CHANGES,
        States.rejected: ADMIN_UPDATE,
        States.archived: ADMIN_UPDATE,
    },
    States.rejected: {
        States.initial: ADMIN_UPDATE,
        States.approved: ADMIN_UPDATE,
        States.rejected: ADMIN_UPDATE,
        States.archived: ADMIN_UPDATE,
    },
    States.archived: {
        States.initial: ADMIN_UPDATE,
        States.approved: ADMIN_UPDATE,
        States.rejected: ADMIN_UPDATE,
        States.archived: ADMIN_UPDATE,
    },
}

def get_state_transition(machine: dict, from_state: str, to_state: str) -> dict:
    return machine.get(from_state, {}).get(to_state, {})
