import json
from boto3.dynamodb.conditions import Key

from lib import ncr_util, authz
from lib.logger import logger
from lib.lambda_decorator.decorator import api_decorator
from lib.lambda_decorator.scan_id_decorator import get_scan_id_decorator
from lib.lambda_decorator.email_decorator import email_decorator
from lib.dynamodb import ncr_table, requirements_table


@api_decorator
@email_decorator
@get_scan_id_decorator
def ncr_handler(event, context):
    scan_id = event['scanId']
    user = event['userRecord']

    multivalue_querystring_parameters = event.get('multiValueQueryStringParameters') or {}
    querystring_parameters = event.get('queryStringParameters') or {}
    account_ids = multivalue_querystring_parameters.get('accountId', [])
    requirement_id = querystring_parameters.get('requirementId', False)
    logger.debug('Account Ids: %s', json.dumps(account_ids, default=str))
    logger.debug('Requirement ID: %s', json.dumps(requirement_id, default=str))
    authz.require_can_read_account(user, account_ids)

    # get requirements
    if requirement_id:
        requirements = {
            requirement_id: requirements_table.get(requirement_id)
        }
    else:
        all_requirements = requirements_table.scan_all()
        requirements = {}
        for requirement in all_requirements:
            requirements[requirement['requirementId']] = requirement
    logger.debug('Requirements: %s', json.dumps(requirements, default=str))

    ncr_records, to_parse = [], []
    for account_id in account_ids:
        if isinstance(requirement_id, str):
            to_parse = ncr_table.query_all(
                IndexName='by-scanId',
                KeyConditionExpression=Key('scanId').eq(scan_id) &
                Key('rqrmntId_accntId').eq(
                    '{}#{}'.format(requirement_id, account_id)
                )
            )
        else:
            to_parse = ncr_table.query_all(
                KeyConditionExpression=Key('scanId').eq(scan_id) &
                Key('accntId_rsrceId_rqrmntId').begins_with(account_id)
            )
        logger.debug('To parse: %s', json.dumps(to_parse, default=str))

        for item in to_parse:
            ncr = prepare_allowed_actions_output(initialize_output(scan_id, item), item, user, account_id, requirements[item['requirementId']])
            ncr_records.append(prepare_resource_output(ncr, item))

    return {'ncrRecords': ncr_records}

##########
##-PREP-##
##########
def initialize_output(scan_id, resource):
    """
    Method to create the initial dict based on scan_id and resource.

    :param scan_id: String representing the scan id for this run.
    :param resource: a dict representing the resource to configure the id from.

    :returns dict: A dict with the ncrId only combining the scan_id and ncr unique identifier.
    """
    return {'ncrId': ncr_table.create_ncr_id(resource)}

def prepare_allowed_actions_output(output, resource, user, account, requirement):
    """
    Method to build the allowedActions section of the output.

    :param output: The output to append the allowedActions to.
    :param resource: a dict representing the resource to configure the id from.
    :param user: a dict representing the user which the dict is being built for.
    :param account: a string representing the account.
    :param requirement: a dict representing the requirement.

    :returns dict: A dict combining the output parameter passed in and the generated allowedActions dict.
    """
    output['allowedActions'] = ncr_util.get_allowed_actions(user, account, requirement, resource.get('exclusion', {}))
    return output

def prepare_resource_output(output, resource):
    """
    Method to build the resource section of the output.

    :param output: The output to append the resource to.
    :param resource: a dict representing the resource to configure the id from.

    :returns dict: A dict combining the output parameter passed in and the generated resource dict.
    """
    new_resource = dict(resource)
    if 'scanId' in new_resource:
        del new_resource['scanId']
    if 'accntId_rsrceId_rqrmntId' in new_resource:
        del new_resource['accntId_rsrceId_rqrmntId']
    if 'rqrmntId_accntId' in new_resource:
        del new_resource['rqrmntId_accntId']

    output['resource'] = new_resource
    return output
