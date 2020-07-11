"""Module concerned with the implementation of POST /remediate endpoint. The 'managing function'
contained here is exposed via the api endpoint, but the actual remediation itself is performed by a 'worker'
function which is invoked by the handler in this file."""

import json
import os
from datetime import datetime
from typing import Optional, Tuple

import boto3
from botocore.exceptions import ClientError

from lib import authz
from lib.dynamodb import accounts_table, audit_table, config_table, ncr_table, requirements_table
from lib.lambda_decorator.decorator import api_decorator, serializer
from lib.lambda_decorator.email_decorator import email_decorator
from lib.lambda_decorator.exceptions import HttpInvalidException, HttpNotFoundException
from lib.logger import logger
from remediation.workers.worker_base import RemediationStatus, WorkerEvent, WorkerResponse

SNS_ARN = os.getenv('SNS_ARN')

lambda_client = boto3.client('lambda')
sns_client = boto3.client('sns')
boto_sts = boto3.client('sts')


def check_ncr(ncr_id):
    """ensure NCR can be found in ncr table for specified ncrId"""
    try:
        ncr_id_parts = ncr_table.parse_ncr_id(ncr_id)
    except: # pylint: disable=broad-except
        raise HttpInvalidException('invalid NCR ID')
    ncr = ncr_table.get_item(Key={
        'scanId': ncr_id_parts.scan_id,
        'accntId_rsrceId_rqrmntId': ncr_id_parts.accntId_rsrceId_rqrmntId,
    }).get('Item', False)
    if not ncr:
        raise HttpNotFoundException(f'record for ncrId {ncr_id} not found')
    return ncr


def get_roles_arns(account_id) -> Tuple[str, str]:
    """Gets roles arns for remediation and read only"""
    # read only role is cross_account_role
    # remediation role will be constructed from account id and role name, role name from environment variable
    try:
        readonly_arn = accounts_table.get_item(Key={'accountId': account_id})['Item'].get('cross_account_role')
    except KeyError:
        raise HttpNotFoundException(f'no account record found for accountId {account_id}')
    remediation_arn = f'arn:aws:iam::{account_id}:role/{os.getenv("REMEDIATION_ROLE_NAME")}'
    return readonly_arn, remediation_arn


def validate_input(remediation_parameters, remediation):
    if not isinstance(remediation_parameters, dict):
        raise HttpInvalidException('remediation parameters must be a dictionary')
    required_keys = set(remediation['parameters'].keys())
    given_keys = set(remediation_parameters.keys())
    missing_keys = required_keys - given_keys
    extra_keys = given_keys - required_keys
    if missing_keys or extra_keys:
        raise HttpInvalidException(f'Invalid remediation parameters, missing keys: {", ".join(missing_keys)}, extra keys {", ".join(extra_keys)}')

def publish_to_sns(status, message, user, ncr, requirement, parameters):
    """publish message to sns"""
    sns_message = {
        'timestamp': datetime.now().isoformat(),
        'message': message,
        'status': status,
        'user': user,
        'ncr': ncr,
        'requirement': requirement,
        'parameters': parameters,
    }
    sns_response = sns_client.publish(
        TargetArn=SNS_ARN,
        Message=json.dumps(sns_message, default=serializer)
    )
    logger.info('sns_message: %s, sns_response: %s', sns_message, sns_response)

def has_remediation_roles(user_email: str, readonly_role_arn: str, remediation_role_arn: str) -> Tuple[bool, Optional[str]]:
    role_session_name = f'remediation_{user_email}_role_check'
    role_errors = []
    try:
        boto_sts.assume_role(
            RoleArn=readonly_role_arn,
            RoleSessionName=role_session_name
        )
    except ClientError:
        role_errors.append('readonly role')
    try:
        boto_sts.assume_role(
            RoleArn=remediation_role_arn,
            RoleSessionName=role_session_name
        )
    except ClientError as e:
        print(e)
        role_errors.append('remediation role')

    if role_errors:
        return False, f'unable to assume {" and ".join(role_errors)}'

    return True, None

def require_remediation_roles(user_email: str, readonly_role_arn: str, remediation_role_arn: str):
    result, reason = has_remediation_roles(user_email, readonly_role_arn, remediation_role_arn)
    if not result:
        raise HttpInvalidException(f'remediation must be done manually: {reason}')

def invoke_worker(worker_function_name, worker_event):
    status = None
    message = None
    try:
        response = lambda_client.invoke(
            FunctionName=os.getenv('WORKER_PREFIX') + worker_function_name,
            Payload=bytes(json.dumps(worker_event, default=serializer), 'utf-8')
        )
        worker_response: WorkerResponse = json.loads(response['Payload'].read())
        if response.get('FunctionError'):
            status = RemediationStatus.ERROR
            message = json.dumps(worker_response)
        elif worker_response['status'] not in [RemediationStatus.SUCCESS,
                                               RemediationStatus.ERROR,
                                               RemediationStatus.IAC_OVERRIDE_REQUIRED,
                                               RemediationStatus.VALIDATION_ERROR]:
            status = RemediationStatus.ERROR
            message = 'Invalid status code response from remediation'
        else:
            status = worker_response['status']
            message = worker_response['message']
    except ClientError as e:
        logger.warning(e)
        status = RemediationStatus.ERROR
        message = 'Error invoking remediation worker'
    except json.decoder.JSONDecodeError as e:
        logger.warning(e)
        status = RemediationStatus.ERROR
        message = 'Invalid JSON response from remediation'
    except KeyError as e:
        logger.warning(e)
        status = RemediationStatus.ERROR
        message = 'Invalid response from remediation'
    return status, message

@api_decorator
@email_decorator
def remediate_manager_handler(event, context):  # pylint: disable=R1710
    """
    This handler is the managing function, which invokes the various remediation functions.
    :param event: {
      "body": {
        "remediationParameters": dict,
        "ncrId": string,
        "overrideIacWarning": bool,
      }
    }
    """
    user = event['userRecord']
    email = user['email']
    ## Pre remediation checks
    # ensure that ncrId is valid
    ncr_id = event['body']['ncrId']

    ncr = check_ncr(ncr_id)
    # TODO check that ncr belongs to the latest scan

    requirement = requirements_table.get(ncr['requirementId'])
    remediation_parameters = event['body']['remediationParameters']
    remediations = config_table.get_config(config_table.REMEDIATIONS)
    remediation = remediations[requirement.get('remediation', {}).get('remediationId', {})]
    # check that requirement has remediation
    if 'remediation' not in requirement:
        raise HttpInvalidException('No remediation available for this resource type')

    # Validate the input based on the remediation
    validate_input(remediation_parameters, remediation)

    # check that use can request remediated
    authz.can_remediate(user, ncr['accountId'])


    # Validate the both roles are deployed in the target account.
    readonly_role_arn, remediation_role_arn = get_roles_arns(ncr['accountId'])
    require_remediation_roles(email, readonly_role_arn, remediation_role_arn)

    # Update NCR record to indicate remediation in progress
    updated = ncr_table.update_remediation_status(
        {
            'scanId': ncr['scanId'],
            'accntId_rsrceId_rqrmntId': ncr['accntId_rsrceId_rqrmntId'],
        },
        ncr_table.REMEDIATION_IN_PROGRESS,
        check_remediation_started=True
    )
    if not updated:
        return {
            'status': RemediationStatus.ERROR,
            'message': f'remediation for ncrId {event["body"]["ncrId"]} failed as remediation in progress'
        }

    # Add an audit trail record indicating remediation started
    audit_table.put_audit_trail(email, audit_table.REMEDIATION_STARTED, event['body']['remediationParameters'])

    # Invoke the remediation function
    worker_event: WorkerEvent = {
        'remediationParameters': remediation_parameters,
        'requirementBasedParameters': requirement['remediation'].get('requirementBasedParameters', {}),
        'overrideIacWarning': event['body'].get('overrideIacWarning', False),
        'readonlyRoleArn': readonly_role_arn,
        'remediationRoleArn': remediation_role_arn,
        'userEmail': email,
        'ncr': ncr
    }

    status, message = invoke_worker(remediation['lambdaFunctionName'], worker_event)

    if status == RemediationStatus.ERROR:
        audit_status = audit_table.REMEDIATION_ERRORED
        update_remediation_status = ncr_table.REMEDIATION_ERROR
    elif status == RemediationStatus.VALIDATION_ERROR:
        audit_status = audit_table.REMEDIATION_INVALID_INPUT
        update_remediation_status = None # reset remediation status so it can be triggered again
    elif status == RemediationStatus.IAC_OVERRIDE_REQUIRED:
        audit_status = audit_table.REMEDIATION_IAC_OVERRIDE
        update_remediation_status = None # reset remediation status so it can be triggered again
    elif status == RemediationStatus.SUCCESS:
        audit_status = audit_table.REMEDIATION_COMPLETED
        update_remediation_status = ncr_table.REMEDIATION_SUCCESS

    audit_table.put_audit_trail(email, audit_status, remediation_parameters)

    # Publish remediation to an SNS topic if env variable has been set
    if SNS_ARN:
        publish_to_sns(status, message, user, ncr, requirement, remediation_parameters)

    # Update the NCR record
    updated_ncr = ncr_table.update_remediation_status(
        {
            'scanId': ncr['scanId'],
            'accntId_rsrceId_rqrmntId': ncr['accntId_rsrceId_rqrmntId'],
        },
        update_remediation_status,
        check_remediation_started=False
    )

    response = {
        'status': status,
        'message': message,
    }
    if status == RemediationStatus.SUCCESS:
        response['updatedNcr'] = updated_ncr.get('Attributes', {})

    return response
