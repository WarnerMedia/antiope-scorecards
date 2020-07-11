import urllib.parse

from boto3.dynamodb.conditions import Key

from lib.authz import require_can_read_account
from lib.dynamodb import accounts_table, scores_table
from lib.lambda_decorator.decorator import api_decorator
from lib.lambda_decorator.email_decorator import email_decorator
from lib.lambda_decorator.exceptions import HttpInvalidException, HttpNotFoundException
from lib.lambda_decorator.scan_id_decorator import get_scan_id_decorator


@api_decorator
@email_decorator
@get_scan_id_decorator
def account_detailed_scores_handler(event, context):
    """
    :param event:
    :param context:
    :raises HttpInvalidException if missing 'scanId' or 'accountIds':
    :return account scores of all account_ids in event:
    """
    try:
        account_ids = event['pathParameters']['accountIds']
        scan_id = event['scanId']
    except KeyError:
        raise HttpInvalidException('account ids or scan id not found in request')

    accounts = []
    account_ids = urllib.parse.unquote(account_ids).split(',')
    require_can_read_account(event['userRecord'], account_ids)

    for account_id in account_ids:
        try:
            account_name = accounts_table.get_account(account_id).get('account_name', account_id)
        except KeyError:
            raise HttpNotFoundException(f'account record not found for {account_id}')

        if len(account_id) > 0:
            detailed_score = {
                'accountId': account_id,
                'accountName': account_name,
            }
            requirements = []
            to_parse = scores_table.query_all(
                KeyConditionExpression=Key('scanId').eq(scan_id) & Key('accntId_rqrmntId').begins_with(account_id),
            )
            for item in to_parse:
                requirements.append({'requirementId': item['requirementId'], 'score': item['score']})

            detailed_score['requirementsScores'] = requirements
            accounts.append(detailed_score)

    return {'accounts': accounts}
