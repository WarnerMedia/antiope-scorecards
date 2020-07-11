from datetime import datetime, timedelta
from lib.logger import logger
from lib.dynamodb import ncr_table, requirements_table, scans_table
from lib.dict_merge import dict_merge


def account_id(old_exclusion: dict, update_request: dict, exclusion_config: dict, is_admin: bool) -> tuple:
    account = update_request.get('accountId')
    if account == '*':
        if is_admin:
            return True, None
        else:
            return False, 'User endpoint cannot manage wildcard exclusions'
    if len(account) != 12:
        return False, 'accountId must be a valid 12-digit account ID'
    if not account.isnumeric():
        return False, 'accountId must be a numeric string'
    return True, None


def expiration_date(old_exclusion: dict, update_request: dict, exclusion_config: dict, is_admin: bool):
    max_duration_in_days = exclusion_config['maxDurationInDays']
    try:
        expiration = datetime.strptime(update_request['expirationDate'], '%Y/%m/%d')
    except ValueError as err:
        logger.debug('Error parsing datetime %s', err, exc_info=True)
        return False, 'Unable to parse datetime'
    delta = expiration - datetime.now()
    if delta < timedelta():
        return False, 'expirationDate must be in the future'
    if max_duration_in_days <= delta.days:
        return False, f'expirationDate must be less than the configured maxDurationInDays: {max_duration_in_days}'
    return True, None


def resource_id(old_exclusion: dict, update_request: dict, exclusion_config: dict, is_admin: bool):
    if not is_admin:
        if '*' in update_request['resourceId']:
            return False, 'User cannot manage wildcard exclusions'
        latest_scan_id = scans_table.get_latest_complete_scan()
        key = {
            'scanId': latest_scan_id,
            'accntId_rsrceId_rqrmntId': ncr_table.create_sort_key(
                update_request['accountId'],
                update_request['resourceId'],
                update_request['requirementId'],
            ),
        }
        ncr = ncr_table.get_item(Key=key).get('Item', {})
        if not ncr:
            return False, 'Cannot find resource'
    return True, None


def requirement_id(old_exclusion: dict, update_request: dict, exclusion_config: dict, is_admin: bool):
    if '*' in update_request['requirementId']:
        return False, 'Wildcard requirements are not supported'
    if not is_admin:
        requirement = requirements_table.get_item(Key={'requirementId': update_request['requirementId']}).get('Item', {})
        if not requirement:
            return False, 'Requirement not found'
    return True, None


def form_fields(old_exclusion: dict, update_request: dict, exclusion_config: dict, is_admin: bool):
    result = dict_merge(old_exclusion.get('formFields', {}), update_request['formFields'])
    return _validate_form_fields(exclusion_config, result)


def update_requested(old_exclusion: dict, update_request: dict, exclusion_config: dict, is_admin: bool):
    requested_update = update_request['updateRequested']
    if requested_update is None or requested_update == {}:
        return True, None
    valid_update_keys = {'formFields', 'expirationDate'}
    given_update_keys = set(requested_update.keys())
    extra_keys = given_update_keys - valid_update_keys
    if extra_keys:
        return False, {'extraKeys': list(extra_keys)}
    if 'formFields' in requested_update:
        result = dict_merge(old_exclusion.get('formFields', {}), requested_update['formFields'])
        is_valid, message = _validate_form_fields(exclusion_config, result)
        if not is_valid:
            return False, message
    if 'expirationDate' in requested_update:
        max_duration_in_days = exclusion_config['maxDurationInDays']
        try:
            new_expiration = datetime.strptime(requested_update['expirationDate'], '%Y/%m/%d')
        except ValueError as err:
            logger.debug('Error parsing datetime %s', err, exc_info=True)
            return False, 'Unable to parse datetime'
        delta = new_expiration - datetime.now()
        if delta < timedelta():
            return False, 'expirationDate must be in the future'
        if max_duration_in_days <= delta.days:
            return False, f'expirationDate must be less than the configured maxDurationInDays: {max_duration_in_days}'
        return True, None
    return True, None


def admin_comments(old_exclusion: dict, update_request: dict, exclusion_config: dict, is_admin: bool):
    if not isinstance(update_request['adminComments'], str):
        return False, 'Admin comments must be a string'
    return True, None


def hides_resources(old_exclusion: dict, update_request: dict, exclusion_config: dict, is_admin: bool):
    if not isinstance(update_request['hidesResources'], bool):
        return False, 'hidesResources must be a boolean'
    return True, None


def _validate_form_fields(exclusion_config: dict, fields: dict):
    required_keys = set(exclusion_config['formFields'].keys())
    given_keys = set(fields.keys())
    missing_keys = required_keys - given_keys
    extra_keys = given_keys - required_keys
    if missing_keys or extra_keys:
        return False, {
            'message': 'Invalid form fields',
            'missingKeys': list(missing_keys),
            'extraKeys': list(extra_keys),
        }
    return True, None
