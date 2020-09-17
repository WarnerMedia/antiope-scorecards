import os

import boto3
from botocore.exceptions import ClientError

from lib.lambda_decorator.decorator import api_decorator
from lib.lambda_decorator.email_decorator import email_decorator
from lib.lambda_decorator.scan_id_decorator import get_scan_id_decorator
from lib.lambda_decorator import exceptions
from lib.dynamodb import user_table, requirements_table, accounts_table, config_table
from lib.logger import logger

BUCKET = os.environ.get('SCORECARD_BUCKET')
PREFIX = os.environ.get('SCORECARD_PREFIX')

s3 = boto3.client('s3')

def create_presigned_url(bucket_name, object_name):
    """Generate a presigned URL to an S3 object

    :param bucket_name: string
    :param object_name: string
    :return: Presigned URL as string. If error, returns None.
    """
    try:
        response = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_name})
    except ClientError as e:
        logger.error(e)
        return None
    return response

def list_all_users(all_accounts):
    """
    :return: list composed of all users' email, first name, last name, and a list of accountIds associated
    with that user
    """
    users = user_table.scan_all(ProjectionExpression='email, firstName, lastName, accounts')
    for user in users:
        user['accountList'] = [
            {
                'accountId': account,
                'accountName': all_accounts.get(account, {}).get('account_name', '')
            } for account in user.get('accounts', {}).keys()]
        user.pop('accounts', None)
    return users


def create_account_list(accounts):
    """
    :param accounts: full contents of accounts table
    :return: list composed of all accounts (just accountId) in accounts table
    """
    logger.debug('Creating account list')
    return [
        {
            'accountId': account['accountId'],
            'accountName': account.get('account_name', ''),
        } for account in accounts.values()]


def scan_requirements():
    """
    :return: list, composed of each document in requirements table
    """
    return requirements_table.scan()['Items']


def get_payer_accounts(accounts):
    """
    :param accounts: full contents of accounts table
    :return: list of payer objects representing each unique payer id in accounts table
    """
    logger.debug('Getting payer accounts')
    unique_payer_ids = {account.get('payer_id', '') for account in accounts.values()}
    return [make_payer_object(payer_id, accounts) for payer_id in unique_payer_ids if payer_id]


def make_payer_object(payer_id, all_accounts):
    to_return = {}
    accounts = [account for account in all_accounts.values() if account.get('payer_id') == payer_id]
    payer_account = all_accounts.get(payer_id, None)

    to_return['id'] = payer_id
    if payer_account:
        to_return['accountName'] = payer_account.get('account_name', '')
    else:
        to_return['accountName'] = 'not available'
    to_return['accountList'] = [
        {'accountId': account['accountId'], 'accountName': account['account_name']}
        for account in accounts
    ]

    return to_return


@api_decorator
@email_decorator
@get_scan_id_decorator
def user_status_handler(event, _context):
    user = event.get('userRecord')
    if not user:
        return {'isAuthenticated': False}

    scan_id = event['scanId']
    if not scan_id:
        raise exceptions.HttpNotFoundException('No scan found')
    s3_prefix = '{}/by-user/{}.xlsx'.format(PREFIX, user.get('email', ''))
    spreadsheet_url = create_presigned_url(BUCKET, s3_prefix)
    response = {
        'isAuthenticated': True,
        'scan': {
            'lastScanDate': scan_id.split('#')[0],
        },
        'spreadsheetUrl': spreadsheet_url,
    }

    for key in ['email', 'firstName', 'lastName']:
        if key in user:
            response[key] = user[key]
    if 'accounts' in user:
        response['accountList'] = [{'accountId': account} for account in user['accounts'].keys()]

    requirements = scan_requirements()
    remediation_types = config_table.get_config(config_table.REMEDIATIONS)
    for requirement in requirements:
        if isinstance(requirement.get('remediation'), dict):
            remediation_id = requirement['remediation'].get('remediationId')
            remediation = remediation_types.get(remediation_id)
            if remediation:
                requirement['remediation']['parameters'] = remediation['parameters']
    response['requirements'] = requirements

    exclusion_types = config_table.get_config('exclusions')
    if exclusion_types:
        response['exclusionTypes'] = exclusion_types
    severity_colors = config_table.get_config('severityColors')
    if severity_colors:
        response['severityColors'] = severity_colors

    response['isAdmin'] = user.get('isAdmin', False)
    if response['isAdmin']:
        all_accounts = {account['accountId']: account for account in accounts_table.scan_all()}
        response.update({
            'isAdmin': True,
            'usersList': list_all_users(all_accounts),
            'accountList': create_account_list(all_accounts),
            'payerAccounts': get_payer_accounts(all_accounts),
        })
    return response
