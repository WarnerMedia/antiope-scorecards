"""
Contains lambdahandler functions for cloudsploit scanning / population
steps of the scanning step function.
"""
import datetime
import json
import os
from collections import defaultdict
from lib.logger import logger

from lib.dynamodb import requirements_table, accounts_table, ncr_table, scores_table, scans_table
from lib.s3.s3_buckets import S3
from lib.lambda_decorator.decorator import states_decorator


bucket_name = os.getenv('CLOUDSPLOIT_RESULT_BUCKET')
cloudsploit_prefix = os.getenv('CLOUDSPLOIT_PREFIX')

MAX_S3_OBJECT_AGE = datetime.timedelta(hours=24)

def object_expiration_check(s3_response, s3_key):
    last_update_time = s3_response['LastModified'].replace(tzinfo=None)
    if datetime.datetime.utcnow() - last_update_time > MAX_S3_OBJECT_AGE:
        raise Exception(f's3 object too old, key: {s3_key}, bucket: {bucket_name}')

@states_decorator
def cloudsploit_populate(event, context):
    """
    Import cloudsploit findings from s3 and convert to NCRs based on
    requirement definitions

    Expected input event format
    {
        scanId: string,
        accountId: string,
    }
    """
    account_id = event['accountId']
    scan_id = event['scanId']
    if not isinstance(scan_id, str):
        raise TypeError(f'scanId should be str, not {type(scan_id)}')

    account = accounts_table.get_account(account_id)

    # keys here will be the ncr's sort key which will uniquely identify it
    # since the partion key will be the scanId for all ncrs created.
    all_ncrs = {}
    scores_to_put = []

    cloudsploit_based_requirements = requirements_table.get_cloudsploit_based_requirements()

    # split requirements based on whether they apply to the account
    applying_requirements, not_applying_requirements = split_requirements(cloudsploit_based_requirements, account)

    s3_key = cloudsploit_prefix + '/' + account_id + '/latest.json'

    # load cloudsploit results
    logger.info('Getting Cloudsploit results from s3://%s/%s', bucket_name, s3_key)
    response = S3.get_object(Bucket=bucket_name, Key=s3_key)
    object_expiration_check(response, s3_key)
    result = json.loads(response['Body'].read())


    # group cloudsploit results by finding
    grouped_results_data = defaultdict(list)
    for result_object in result['resultsData']:
        grouped_results_data[result_object['title']].append(result_object)

    # add NCRs based on cloudsploit requirements
    for requirement in applying_requirements:
        requirement_titles = requirement['cloudsploit']['finding']
        if isinstance(requirement_titles, str):
            requirement_titles = [requirement_titles]
        relevant_results = []
        for requirement_title in requirement_titles:
            relevant_results.extend(grouped_results_data.get(requirement_title, []))

        failing_statuses = determine_failing_statuses(requirement)

        # create NCR for each cloudsploit result
        for finding_object in relevant_results:
            if finding_object['status'] in failing_statuses:

                # set resource if cloudsploit didn't provide one
                if finding_object['resource'] == ncr_table.CLOUDSPLOIT_FINDING_NA and requirement['cloudsploit'].get('regional', False) is True:
                    resource_id = finding_object['region']
                elif finding_object['resource'] == ncr_table.CLOUDSPLOIT_FINDING_NA:
                    resource_id = str(account_id)
                else:
                    resource_id = extract_resource_id(finding_object['resource'])

                ncr_key = ncr_table.create_sort_key(account_id, resource_id, requirement['requirementId'])
                if ncr_key in all_ncrs:
                    all_ncrs[ncr_key]['reason'][finding_object['message']] = None
                else:
                    all_ncrs[ncr_key] = ncr_table.new_ncr_record(
                        {
                            'accountId': account_id,
                            'accountName': account['account_name'],
                            'requirementId': requirement['requirementId'],
                            'resourceId': resource_id,
                            'resourceType': finding_object['category'],
                            'region': finding_object['region'],
                            'reason': {finding_object['message']: None}, # dict as set with 1 item (set to deduplicate reasons)
                            'cloudsploitStatus': finding_object['status'] # Send the cloudsploit status to the NCR Record
                        },
                        scan_id
                    )

        # determine number of resources for score
        if requirement['cloudsploit'].get('source'):
            service_name, api_call = requirement['cloudsploit'].get('source').split('.')
            cloudsploit_data = result['collectionData']['aws'][service_name][api_call]
            try:
                num_resources = sum(len(region_object['data']) for region_object in cloudsploit_data.values() if 'err' not in region_object)
            except KeyError:
                raise RuntimeError(f'{service_name}, {api_call} collectionData contained region object lacking both "data" and "err" keys"')
        else:
            num_resources = len(relevant_results)

        scores_to_put.append(scores_table.new_score(scan_id, account_id, requirement, num_resources))
    # add N/A score for requirements that don't apply
    for requirement in not_applying_requirements:
        scores_to_put.append(scores_table.new_score(scan_id, account_id, requirement, scores_table.NOT_APPLICABLE, scores_table.NOT_APPLICABLE))

    for ncr in all_ncrs.values():
        ncr['reason'] = '\n'.join(ncr['reason'].keys())
        logger.info('Adding ncrs: %s', json.dumps(all_ncrs))
    ncr_table.batch_put_records(all_ncrs.values())
    scores_table.batch_put_records(scores_to_put)


@states_decorator
def cloudsploit_setup(event, context):
    """
    Create parameters for external cloudsploit scanning lambda based on
    account settings and requirement definition.

    Expected input event format
    {
        'accountId': account_id,
        'scanId': scan_id,
        'cloudsploitSettingsMap': {
            'default': {...},
            'settings1': {...},
            ...
        }
    }
    """
    account = accounts_table.get_account(event['accountId'])
    if 'cross_account_role' not in account:
        raise ValueError(f'cross_account_role not specified in account {event["accountId"]}')
    cross_account_role = account.get('cross_account_role', None)
    if 'scorecard_profile' in account:
        try:
            settings = event['cloudsploitSettingsMap'][account['scorecard_profile']]
        except KeyError:
            raise KeyError(f'cloudsploit settings {account["scorecard_profile"]} specified in {event} does not exist')
    else:
        settings = event['cloudsploitSettingsMap']['default']
    return {
        'aws': {
            'roleArn': cross_account_role
        },
        'settings': settings,
        's3Prefix': event['accountId']
    }


@states_decorator
def cloudsploit_error(event, context):
    """
    Handle errors in cloudsploit setup or populate. Invoked by step function.
    Adds a DNC score for each cloudsploit based requirement for the account
    that failed. Also records error in scan record.

    Expected input event format
    {
        'accountId': account_id,
        'scanId': scan_id,
    }
    """
    account_id = event['accountId']
    scan_id = event['scanId']
    error = event['error']
    # remove traceback for cloudsploit errors
    try:
        error['Cause'] = json.dumps({**json.loads(error['Cause']), 'trace': None})
    except: # pylint: disable=bare-except
        pass
    account = accounts_table.get_account(account_id)

    cloudsploit_based_requirements = requirements_table.get_cloudsploit_based_requirements()

    applying_requirements, not_applying_requirements = split_requirements(cloudsploit_based_requirements, account)

    scores_to_put = []
    for requirement in applying_requirements:
        scores_to_put.append(
            scores_table.new_score(
                scan_id,
                account_id,
                requirement,
                scores_table.DATA_NOT_COLLECTED,
                scores_table.DATA_NOT_COLLECTED,
            )
        )
    for requirement in not_applying_requirements:
        scores_to_put.append(
            scores_table.new_score(
                scan_id,
                account_id,
                requirement,
                scores_table.NOT_APPLICABLE,
                scores_table.NOT_APPLICABLE,
            )
        )

    scores_table.batch_put_records(scores_to_put)
    scans_table.add_error(scan_id, context.function_name, event['error'])

def split_requirements(requirements, account):
    """Filters requirements list into two lists, one that applies to the account, the other that does not"""
    applying_requirements = []
    not_applying_requirements = []
    for requirement in requirements:
        if requirements_table.check_requirement_applies_to_account(requirement, account):
            applying_requirements.append(requirement)
        else:
            not_applying_requirements.append(requirement)
    return applying_requirements, not_applying_requirements

def determine_failing_statuses(requirement_object: dict) -> list:
    failing_statuses = []
    if requirement_object['cloudsploit'].get('treatWarnAsPass') is not True:
        failing_statuses.append('WARN')
    if requirement_object['cloudsploit'].get('treatUnknownAsPass') is not True:
        failing_statuses.append('UNKNOWN')
    if requirement_object['cloudsploit'].get('treatFailAsPass') is not True:
        failing_statuses.append('FAIL')
    return failing_statuses


def extract_resource_id(arn):
    # Cloudsploit typically returns ARNs and not resource names/ids. Scorecards are best shown with just the resource id
    # Convert the ARN to just a resource ID.
    # AWS ARN format is defined here: https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
    # Additionally, Cloudsploit extended the ARN format for access keys.
    # an IAM user could be: arn:aws:iam::ACCOUNTID:user/USERNAME
    #                   or: arn:aws:iam::ACCOUNTID:user/USERNAME:access_key_X
    arn_parts = arn.split(':')
    if len(arn_parts) == 6:
        # Arn is either arn:partition:service:region:account-id:resource-id
        #            or arn:partition:service:region:account-id:resource-type/resource-id
        if '/' not in arn_parts[5]:
            resource_id = arn_parts[5]
        else:
            resource_id = arn_parts[5].split('/', 1)[1]  # extract off the resource-type and discard
    elif len(arn_parts) == 7:
        # Arn is either arn:partition:service:region:account-id:resource-type:resource-id
        #            or arn:partition:service:region:account-id:user/USERNAME:access_key_X
        if arn_parts[2] == 'iam':
            username = arn_parts[5].split('/', 1)[1]  # extract off the resource-type and discard
            resource_id = f'{username}-({arn_parts[6]})' # Make the resource_id "username-(access_key_X)"
        else:
            resource_id = arn_parts[6]
    else:
        # Well crap, this is unexpected
        resource_id = arn
    return resource_id
