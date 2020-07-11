import datetime
import os
import urllib.parse

from boto3.dynamodb.conditions import Key

from lib.authz import require_can_read_account
from lib.dynamodb import account_scores_table, accounts_table, scores_table
from lib.lambda_decorator.decorator import api_decorator
from lib.lambda_decorator.email_decorator import email_decorator
from lib.lambda_decorator.exceptions import HttpInvalidException, HttpNotFoundException
from lib.s3.s3_buckets import S3

BUCKET = os.environ.get('SCORECARD_BUCKET')
PREFIX = os.environ.get('SCORECARD_PREFIX')

MONDAY = 0
HISTORICAL_SCORE_COUNT = 6
CRITICAL_SEVERITY = 'critical'

def make_account_object(account_id):
    """
    :param account_id: the account_id of the required score summary
    :return: for each account specified, returns historical score, current score, accountName and
             Download link to latest spreadsheet (presigned s3 url)
    """
    accountscores_records = account_scores_table.query_all(
        KeyConditionExpression=Key('accountId').eq(account_id),
        ScanIndexForward=False
    )

    historical_scores = []

    if accountscores_records:
        current_score = scores_table.get_single_score_calc(accountscores_records[0]['score'])
        critical_count = accountscores_records[0]['score'].get(CRITICAL_SEVERITY, {}).get('numFailing', 0)
        for record in accountscores_records[1:]:
            if datetime.datetime.strptime(record['date'], '%Y-%m-%d').weekday() == MONDAY and len(
                    historical_scores) < HISTORICAL_SCORE_COUNT:
                historical_scores.append({
                    'date': record['date'],
                    'score': scores_table.get_single_score_calc(record['score'])
                })
    else:
        current_score = None
        critical_count = None

    try:
        account_name = accounts_table.get_item(
            Key={'accountId': account_id})['Item'].get('account_name', account_id)
    except KeyError:
        raise HttpNotFoundException(f'account record not found for {account_id}')

    return {
        'accountId': account_id,
        'accountName': account_name,
        'currentScore': current_score,
        'criticalCount': critical_count,
        'historicalScores': historical_scores,
        'spreadsheetDownload': {
            'url': S3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': BUCKET,
                    'Key': '{}/by-account/{}.xlsx'.format(PREFIX, account_id)},
                ExpiresIn=3600  # expiration time set to 1 hour
            )
        }
    }


@api_decorator
@email_decorator
def account_summary_handler(event, context=None):
    """
    :param event: aws lambda event
    :param context: aws lambda context
    :return: a dict with the information on the accountIds
    """
    try:
        account_ids = event['pathParameters']['accountIds']
    except KeyError:
        raise HttpInvalidException('missing account ids')

    account_ids = urllib.parse.unquote(account_ids).split(',')
    require_can_read_account(event['userRecord'], account_ids)

    return {
        'accounts': [make_account_object(account_id) for account_id in account_ids]
    }
