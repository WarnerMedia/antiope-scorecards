"""
The handler function contained in this module
runs in the event that an iteration of the
S3 Import function failed, and this function
updates the score for the failed requirement
for all accounts.
"""
from lib.dynamodb import requirements_table, scans_table, scores_table
from lib.lambda_decorator.decorator import states_decorator


@states_decorator
def s3import_error_handler(event, context=None):
    """
    Creates DNC scores for all accounts for the provided
    requirement id

    Expected input event format
    {
       "scanId": scan_id,
       "requirementId": requirement_id
    }

    """
    scan_id = event['scanId']
    requirement_id = event['requirementId']
    requirement_def = requirements_table.get_item(Key={'requirementId': requirement_id})['Item']
    unique_account_ids = set(event['accountIds'])

    if not isinstance(scan_id, str):
        raise TypeError(f'scanId should be str, not {type(scan_id)}')

    scores_to_put = []

    for missing_account in unique_account_ids:
        scores_to_put.append(
            scores_table.new_score(
                scan_id,
                missing_account,
                requirement_def,
                scores_table.DATA_NOT_COLLECTED,
                scores_table.DATA_NOT_COLLECTED
            )
        )
    scores_table.batch_put_records(scores_to_put)

    scans_table.add_error(event['scanId'], context.function_name, event['error'])
