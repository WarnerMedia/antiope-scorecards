"""These functions call the function they are paired with. If user is or can then these "required" function return nothing.
If the user isn't or can't then these "required" functions raise an appropriate HttpException constructed using the message from the inner function."""

from lib.lambda_decorator.exceptions import HttpForbiddenException

def is_user(user):
    """
    Validates user dict exists.
    :param user: A dict object representing user
    :return (bool, str): Bool for whether or not user is valid, String for justification.
    """
    return (True, None) if user else (False, 'No user found')

def is_admin(user):
    """
    :param user:
    :return True, (str): if user is admin
    :return False, (str): is user is not admin
    """
    if 'isAdmin' in user and user['isAdmin'] is True:
        return True, None
    return False, 'user is not authorized'

def can_read_account(user, account_ids):
    """
    :param user:
    :param account_ids:
    :return from is_admin() function if result is True:
    :return False, (str): if user not allowed access to specific account
    :return False, (str): if missing user record
    :return True, (str): if user has access to all accounts
    """
    if isinstance(account_ids, str):
        account_ids = [account_ids]

    result, reason = is_admin(user)
    if result:
        return result, reason
    else:
        valid_ids = user.get('accounts', {})
        for account_id in account_ids:
            if account_id not in valid_ids.keys():
                return False, 'user is not authorized for account ' + account_id
        return True, None
    return False, None

def can_request_exclusion(user, account_id):
    """
    Checks whether user can request exclusion against a specific account.
    :param user: A dict object representing user
    :param account: A string representing an AWS account to validate permission for.
    :return (bool, str): Bool for whether or not permission exists, String for justification.
    """
    result, reason = is_admin(user)
    if result:
        return result, reason
    return can_user_perform(user, account_id, 'requestExclusion')

def can_remediate(user, account_id):
    """
    Checks whether user can initiate remediation against a specific account.
    :param user: A dict object representing user
    :param account: A string representing an AWS account to validate permission for.
    :return (bool, str): Bool for whether or not permission exists, String for justification.
    """
    return can_user_perform(user, account_id, 'triggerRemediation')

def require_can_remediate(user, account_id):
    result, reason = can_remediate(user, account_id)
    if result:
        raise HttpForbiddenException(f'authorization failed: {reason}')

def can_user_perform(user, account_id, action):
    """
    Utility method for checking arbitrary actions are applicable to a specific account for a user.
    :param user: A dict object representing user
    :param account: A string representing an AWS account to validate permission for.
    :param action: A string representing an action to check for.
    :return (bool, str): Bool for whether or not permission exists, String for justification.
    """
    if 'accounts' in user and account_id in user['accounts']:
        if 'permissions' in user['accounts'][account_id] and action in user['accounts'][account_id]['permissions']:
            if user['accounts'][account_id]['permissions'][action]:
                return True, 'User has explicit permission for account {}.'.format(account_id)

    return False, 'User does not have rights for account {}.'.format(account_id)

def require_can_read_account(user, account_ids):
    """
    :param user:
    :param account_ids:
    :return raises error: if there is a failed auth check
    """
    result, reason = can_read_account(user, account_ids)
    if result is False:
        raise HttpForbiddenException(reason)

def require_is_admin(user):
    result, reason = is_admin(user)
    if result is False:
        raise HttpForbiddenException(reason)

def require_can_request_exclusion(user, account_id):
    """
    :param user:
    :param account_id:
    :return raises error: if there is a failed auth check
    """
    result, reason = can_request_exclusion(user, account_id)
    if result is False:
        raise HttpForbiddenException(reason)
