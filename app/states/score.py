"""
Module concerned with calculation of per requirement per account score,
as well as overall account score.
"""
from collections import defaultdict

from boto3.dynamodb.types import Decimal
from boto3.dynamodb.conditions import Key

from lib.dynamodb import account_scores_table, ncr_table, requirements_table, scores_table, accounts_table
from lib.lambda_decorator.decorator import states_decorator

all_requirements = requirements_table.scan_all()


@states_decorator
def score_calc_handler(event, context):
    """
    :param event: {
        scanId: string,
        accountIds: list of accountIds,
    }
    :param context: dict
    :return: None
    """
    scan_id = event['openScan']['scanId']
    account_ids = event['load']['accountIds']
    date = scan_id[0:10]
    all_scores_to_put = []
    all_account_scores = []

    for account_id in account_ids:
        account_name = accounts_table.get_account(account_id).get('account_name')
        scores_to_put = {
            record['requirementId']: record
            for record in scores_table.query_all(
                KeyConditionExpression=Key('scanId').eq(scan_id) & Key('accntId_rqrmntId').begins_with(account_id)
            )
        }
        existing_ncr_records = ncr_table.query_all(
            KeyConditionExpression=Key('scanId').eq(scan_id) & Key('accntId_rsrceId_rqrmntId').begins_with(account_id),
        )

        grouped_ncr_data = defaultdict(list)
        for ncr_object in existing_ncr_records:
            grouped_ncr_data[ncr_object['requirementId']].append(ncr_object)

        for requirement_object in all_requirements:
            severity = requirement_object['severity']
            record_to_edit = scores_to_put.get(requirement_object['requirementId'], False)
            if record_to_edit is False:
                continue  # data not collected for this account for this scan for this requirement, moving on
            score_object = record_to_edit['score'][severity]

            # check if score is DNC if so we skip counting failing resources
            if scores_table.DATA_NOT_COLLECTED in score_object.values():
                continue

            if score_object['numFailing'] is None:
                score_object['numFailing'] = Decimal(0)

            matching_ncrs = grouped_ncr_data.get(requirement_object['requirementId'], [])
            for ncr_record in matching_ncrs:
                is_excluded = ncr_record.get('exclusionApplied', False)
                # TODO handle hidden ncr's also (decrement numResources)
                if is_excluded:
                    continue
                else:
                    score_object['numFailing'] += 1
            all_scores_to_put.append(record_to_edit)

        account_score = {
            'accountId': account_id,
            'accountName': account_name,
            'date': date,
            'scanId': scan_id,
            'score': scores_table.weighted_score_aggregate_calc(scores_to_put.values())
        }
        all_account_scores.append(account_score)

    scores_table.batch_put_records(all_scores_to_put)
    account_scores_table.batch_put_records(all_account_scores)
