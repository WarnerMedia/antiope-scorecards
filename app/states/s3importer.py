"""
This module provides an entry point to the logic for the
S3 Import Map Iterator.
"""
import datetime
import json

from lib.dynamodb import ncr_table, requirements_table, scores_table
from lib.lambda_decorator.decorator import states_decorator
from lib.s3.s3_buckets import S3
from lib.logger import logger

@states_decorator
def s3import_handler(event, context=None):
    """
    Imports NCRs from S3 based on requirement definition.
    Add scores for all accounts for the requirement

    Expected input event format
    {
        "accountIds": list of account_ids
        "scanId": scan_id,
        "requirementId": requirement_id
    }
    """
    all_account_ids = event['accountIds']
    requirement_id = event['requirementId']
    scan_id = event['scanId']
    requirement_def = requirements_table.get_item(Key={'requirementId': requirement_id})['Item']
    s3_key = requirement_def['s3Import']['s3Key']
    s3_import_bucket_name = requirement_def['s3Import']['s3Bucket']
    if requirement_def.get('ignore', False):
        logger.info('Nothing to do. Ignoring s3 import requirement: %s', requirement_id)
        return

    if not isinstance(scan_id, str):
        raise TypeError(f'scanId should be str, not {type(scan_id)}')

    if not isinstance(s3_key, str):
        raise TypeError(f's3key should be str, not {type(s3_key)}')

    response = S3.get_object(Bucket=s3_import_bucket_name, Key=s3_key)
    last_update_time = response['LastModified'].replace(tzinfo=None)
    if datetime.datetime.utcnow() - last_update_time > datetime.timedelta(hours=24):
        raise Exception(f's3 object too old, key: {s3_key}, bucket: {s3_import_bucket_name}')
    result = json.loads(response['Body'].read())

    ncrs_to_put = []
    scores_to_put = []

    for account_id, import_object in result.items():
        num_resources = import_object['totalResourceCount']

        try:
            all_account_ids.remove(account_id)
        except ValueError:
            logger.warning('Account %s found in import but not present in accounts table', account_id)

        for failing_resource in import_object['failingResources']:
            failing_resource['requirementId'] = requirement_id  # overwrite reqId from import_object
            ncrs_to_put.append(
                ncr_table.new_ncr_record(failing_resource, scan_id)
            )
        scores_to_put.append(
            scores_table.new_score(scan_id, account_id, requirement_def, num_resources)
        )

    for missing_account in all_account_ids:  # accounts present in the s3 import were removed from this list
        scores_to_put.append(
            scores_table.new_score(
                scan_id,
                missing_account,
                requirement_def,
                scores_table.DATA_NOT_COLLECTED,
                scores_table.DATA_NOT_COLLECTED
            )
        )
    ncr_table.batch_put_records(ncrs_to_put)
    scores_table.batch_put_records(scores_to_put)
