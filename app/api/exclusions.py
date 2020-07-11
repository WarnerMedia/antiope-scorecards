import json
from lib import base64
from lib import authz
from lib import ncr_util
from lib.logger import logger
from lib.dict_merge import dict_merge
from lib.lambda_decorator.email_decorator import email_decorator
from lib.lambda_decorator.decorator import api_decorator
from lib.lambda_decorator import exceptions
from lib.lambda_decorator.scan_id_decorator import get_scan_id_decorator
from lib.dynamodb import exclusions_table, audit_table, ncr_table, requirements_table, config_table
from lib.exclusions import exclusions
from states.exclude import update_ncr_exclusion

@api_decorator
@email_decorator
def get_exclusions_handler(event, context):
    authz.require_is_admin(event.get('userRecord'))
    scan_params = {}
    querystring_parameters = event.get('queryStringParameters') or {}
    try:
        next_token = querystring_parameters.get('nextToken')
        if next_token:
            scan_params['ExclusiveStartKey'] = json.loads(base64.base64_to_string(next_token))
    except Exception: # pylint: disable=broad-except
        pass
    try:
        limit = querystring_parameters.get('limit')
        if limit:
            scan_params['Limit'] = int(limit)
    except Exception: # pylint: disable=broad-except
        pass

    result = exclusions_table.scan(**scan_params)
    exclusions = result['Items']
    for exclusion in exclusions:
        exclusion['exclusionId'] = exclusions_table.get_exclusion_id(exclusion)
    last_evaluated_key = None
    if 'LastEvaluatedKey' in result:
        last_evaluated_key = base64.string_to_base64(json.dumps(result['LastEvaluatedKey']))

    return {
        'exclusions': exclusions,
        'nextToken': last_evaluated_key,
    }


@api_decorator
@email_decorator
@get_scan_id_decorator
def put_exclusions_handler(event, context):
    user_record = event.get('userRecord', {})
    authz.require_is_admin(user_record)
    body = event.get('body', {})
    current_exclusion_id = body.get('exclusionId', '')
    update_request = body.get('exclusion', {})
    if current_exclusion_id:
        _, requirement_id, _ = split_exclusion_id(current_exclusion_id)
    else:
        requirement_id = update_request.get('requirementId', '')

    # input validation
    if not update_request:
        raise exceptions.HttpInvalidException('Must supply exclusion to put')

    # data validation
    current_exclusion = get_current_exclusion(current_exclusion_id)
    prospective_exclusion = dict_merge(current_exclusion, update_request)
    target_account_id = prospective_exclusion.get('accountId')
    delete_exclusion = current_exclusion if update_requires_replacement(current_exclusion, update_request) else {}
    requirement = requirements_table.get(requirement_id)
    exclusion_type = requirement.get('exclusionType')
    exclusion_config = config_table.get_config(config_table.EXCLUSIONS).get(exclusion_type)
    logger.debug('%s', json.dumps({
        'current_exclusion': current_exclusion,
        'prospective_exclusion': prospective_exclusion,
        'target_account_id': target_account_id,
        'delete_exclusion': delete_exclusion,
        'requirement': requirement,
        'exclusion_type': exclusion_type,
        'exclusion_config': exclusion_config,
    }, default=str))
    if not requirement:
        raise exceptions.HttpNotFoundException(f'Requirement not found: {requirement_id}')
    if not exclusion_config:
        raise exceptions.HttpInvalidException(f'Cannot find exclusion type: {exclusion_type}')

    # authorization
    authz.require_can_request_exclusion(user_record, target_account_id)

    new_exclusion = exclusions.update_exclusion(current_exclusion, update_request, exclusion_config, True)
    if new_exclusion:
        new_exclusion['exclusionId'] = exclusions_table.get_exclusion_id(new_exclusion)
        new_exclusion['lastModifiedByAdmin'] = user_record.get('email')
        new_exclusion['rqrmntId_rsrceRegex'] = '#'.join([requirement_id, new_exclusion['resourceId']])
        new_exclusion['type'] = exclusion_type
    if delete_exclusion:
        delete_exclusion['exclusionId'] = exclusions_table.get_exclusion_id(delete_exclusion)
    exclusions_table.update_exclusion(new_exclusion, delete_exclusion)

    if user_record.get('email'):
        audit_table.put_audit_trail(user_record['email'], audit_table.PUT_EXCLUSION_ADMIN, {
            'updateRequest': update_request,
            'newExclusion': new_exclusion,
            'deleteExclusion': delete_exclusion,
        })

    return {
        'newExclusion': new_exclusion,
        'deleteExclusion': delete_exclusion,
    }


@api_decorator
@email_decorator
@get_scan_id_decorator
def put_exclusions_for_user_handler(event, context):
    latest_scan_id = event.get('scanId', '')
    user_record = event.get('userRecord', {})
    body = event.get('body', {})
    ncr_id = body.get('ncrId', '')
    update_request = body.get('exclusion', {})
    scan_id, account_id, resource_id, requirement_id = split_ncr_id(ncr_id)

    # input validation
    if scan_id != latest_scan_id:
        raise exceptions.HttpInvalidException('Can only exclude ncrs from latest scans')
    if not update_request:
        raise exceptions.HttpInvalidException('Must supply exclusion to put')

    # data validation
    requirement = requirements_table.get(requirement_id)
    ncr = ncr_table.get_ncr(scan_id, account_id, resource_id, requirement_id)
    current_exclusion = exclusions_table.get_exclusion(account_id=account_id, requirement_id=requirement_id, resource_id=resource_id)
    exclusion_type = requirement.get('exclusionType')
    exclusion_types = config_table.get_config(config_table.EXCLUSIONS)
    exclusion_config = exclusion_types.get(exclusion_type, {})
    if not requirement:
        raise exceptions.HttpNotFoundException(f'Requirement not found: {requirement_id}')
    if not ncr:
        raise exceptions.HttpNotFoundException(f'NCR does not exist: {ncr_id}')
    if not exclusion_config:
        raise exceptions.HttpInvalidException(f'Cannot find exclusion type: {exclusion_type}')

    # authorization
    if exclusions.is_wildcard_exclusion(current_exclusion):
        raise exceptions.HttpForbiddenException('Wildcard exclusion applied to ncr')
    allowed_actions = ncr_util.get_allowed_actions(user_record, account_id, requirement, current_exclusion)
    prospective_exclusion = dict_merge(current_exclusion, update_request)
    prospective_state = exclusions.get_state(prospective_exclusion)
    if prospective_state in exclusions.REQUEST_EXCLUSION_STATES:
        if not allowed_actions['requestExclusion']:
            raise exceptions.HttpForbiddenException('Cannot requestExclusion')
    if prospective_state in exclusions.REQUEST_EXCLUSION_CHANGE_STATES:
        if not allowed_actions['requestExclusionChange']:
            raise exceptions.HttpForbiddenException('Cannot requestExclusionChange')

    # update
    new_exclusion = exclusions.update_exclusion(current_exclusion, update_request, exclusion_config, False)
    new_exclusion['accountId'] = account_id
    new_exclusion['resourceId'] = resource_id
    new_exclusion['requirementId'] = requirement_id
    new_exclusion['type'] = exclusion_type
    new_exclusion['exclusionId'] = exclusions_table.get_exclusion_id(new_exclusion)
    new_exclusion['lastModifiedByUser'] = user_record.get('email')
    new_exclusion['rqrmntId_rsrceRegex'] = f'{new_exclusion["requirementId"]}#{new_exclusion["resourceId"]}'
    exclusions_table.update_exclusion(new_exclusion, {})

    if user_record.get('email'):
        audit_table.put_audit_trail(user_record['email'], audit_table.PUT_EXCLUSION_USER, {
            'updateRequest': update_request,
            'newExclusion': new_exclusion,
            'deleteExclusion': {},
        })

    new_allowed_actions = ncr_util.get_allowed_actions(user_record, account_id, requirement, new_exclusion)
    updated_ncr = update_ncr_exclusion(ncr, new_exclusion, exclusion_types)
    logger.debug('Updated ncr: %s', json.dumps(updated_ncr, default=str))
    ncr_table.put_item(Item=updated_ncr)

    return {
        'newExclusion': new_exclusion,
        'newNcr': {
            'ncrId': ncr_id,
            'resource': updated_ncr,
            'allowedActions': new_allowed_actions,
        }
    }


def split_exclusion_id(exclusion_id: str) -> tuple:
    try:
        parts = exclusions_table.parse_exclusion_id(exclusion_id)
    except TypeError:
        raise exceptions.HttpInvalidException('Invalid exclusionId')
    account_id, requirement_id, resource_id = parts
    return account_id, requirement_id, resource_id


def split_ncr_id(ncr_id: str) -> tuple:
    try:
        parts = ncr_table.parse_ncr_id(ncr_id)
    except TypeError:
        raise exceptions.HttpInvalidException('Invalid ncrId')
    scan_id_date, scan_id_randomness, account_id, resource_id, requirement_id = parts
    scan_id = '#'.join([scan_id_date, scan_id_randomness])
    return scan_id, account_id, resource_id, requirement_id


def get_current_exclusion(exclusion_id: str) -> dict:
    if exclusion_id:
        current_exclusion = exclusions_table.get_exclusion(exclusion_id=exclusion_id)
        if not current_exclusion:
            raise exceptions.HttpNotFoundException(f'Exclusion {exclusion_id} not found')
        return current_exclusion
    else:
        return {}


def update_requires_replacement(current_exclusion, update_request) -> bool:
    if not current_exclusion:
        return False
    key_updates = {'accountId', 'requirementId', 'resourceId'} & set(update_request.keys())
    if key_updates:
        logger.debug('Requested update of a key part/value')
        prospective_merge = dict_merge(current_exclusion, update_request)
        if exclusions_table.get_exclusion_id(prospective_merge) != exclusions_table.get_exclusion_id(current_exclusion):
            logger.debug('Provided an exclusion update that would update the exclusion ID, adding delete_exclusion to transaction items')
            return True
    return False
