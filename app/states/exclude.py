"""
The exclude step applies exclusions to NCRs.
"""
from collections import defaultdict
from datetime import datetime
from fnmatch import fnmatch
from functools import partial
from typing import Callable, Iterable, List

from boto3.dynamodb.conditions import Key

from lib.dynamodb import config_table, exclusions_table, ncr_table
from lib.lambda_decorator.decorator import states_decorator
from lib.logger import logger


def group_exclusions(exclusions: Iterable) -> defaultdict:
    """
    Group exclusions in to nested dictionaries by requirementId and by accountId.
    Access via grouped_exclusions[requirementId][accountId]
    """
    grouped_exclusions = defaultdict(lambda: defaultdict(list))
    for exclusion in exclusions:
        grouped_exclusions[exclusion['requirementId']][exclusion['accountId']].append(
            exclusion
        )
    return grouped_exclusions


def exclusion_prioritizer(exclusion_types: dict, exclusion: dict) -> int:
    """Provide a priority for an exclusion in case multiple exclusions match an NCR"""
    priority = 0

    # effective exclusions have the highest priority
    if is_effective(exclusion_types, exclusion):
        priority += 100

    # then exclusions with a wildcard for the account
    if exclusion['accountId'] == '*':
        priority += 10

    # finally exclusions with a wildcard in the resource id
    if '*' in exclusion['resourceId']:
        priority += 1

    # invert the priority to sort in reverse order
    return -priority


def is_effective(exclusion_types: dict, exclusion: dict) -> bool:
    """Determine if exclusion is effective (e.g. makes an NCR not count against the score)"""
    # check error cases
    if exclusion == {}:
        logger.info('malformed exclusion object')
        return False
    elif 'status' not in exclusion or 'expirationDate' not in exclusion:
        logger.info('exclusion for requirement %s account %s resource %s has no "status" and/or "expirationDate" fields, therefore not effective',
                    exclusion['requirementId'], exclusion['accountId'], exclusion['resourceId'])
        return False

    # check expiration
    if datetime.now() >= datetime.strptime(exclusion['expirationDate'], '%Y/%m/%d'):
        return False

    # return based on status
    if exclusion['status'] == 'approved':
        return True
    elif exclusion['status'] == 'initial':
        # Whether an exclusion in the Initial state is effective is a setting on the exclusion type
        if exclusion_types[exclusion['type']]['states']['initial']['effective']:
            return True
    return False


def pick_exclusion(matched_exclusions: List, exclusion_prioritizer_function: Callable) -> dict:
    """Returns the highest priority exclusion"""
    if len(matched_exclusions) > 0:
        sorted_exclusions = sorted(matched_exclusions, key=exclusion_prioritizer_function)
        return sorted_exclusions[0]
    return {}


def match_exclusions(ncr: dict, grouped_exclusions: defaultdict) -> list:
    """
    Finds exclusions that match on
    requirement id exactly and
    account id (account Id exact match or '*') and
    resource id pattern

    Does not match any exclusions in the archived state.

    Returns list of matching exclusions
    """
    partially_matched_exclusions = (
        grouped_exclusions[ncr['requirementId']]['*'] +
        grouped_exclusions[ncr['requirementId']][ncr['accountId']]
    )
    # return exlusions that match on the resourceId (supports ? and * wildcards) and are not archived
    return [e for e in partially_matched_exclusions
            if fnmatch(ncr['resourceId'], e['resourceId'])
            and e['status'] != 'archived']


def update_ncr_exclusion(ncr: dict, exclusion: dict, exclusion_types: dict) -> dict:
    """Apply exclusion to NCR"""
    effective = is_effective(exclusion_types, exclusion)

    ncr['isHidden'] = exclusion.get('hidesResources', False) and effective
    ncr['exclusionApplied'] = effective
    ncr['exclusion'] = exclusion
    return ncr


@states_decorator
def exclude_handler(event, context):
    """
    Find and apply matching exclusion for all NCRs

    Expected input event format
    {
        "scanId": scan_id,
    }
    """
    exclusion_types = config_table.get_config(config_table.EXCLUSIONS)
    ncrs = ncr_table.query_all(KeyConditionExpression=Key('scanId').eq(event['openScan']['scanId']))

    all_exclusions = exclusions_table.scan_all()
    grouped_exclusions = group_exclusions(all_exclusions)
    logger.info('Found %s exclusions', len(all_exclusions))

    ncr_updated_count = 0
    partial_exclusion_prioritizer = partial(exclusion_prioritizer, exclusion_types)

    records = []
    for ncr in ncrs:
        matched_exclusions = match_exclusions(ncr, grouped_exclusions)

        ncr_exclusion = pick_exclusion(matched_exclusions, partial_exclusion_prioritizer)
        if ncr_exclusion:
            updated_ncr = update_ncr_exclusion(ncr, ncr_exclusion, exclusion_types)
            ncr_updated_count += 1
            records.append(updated_ncr)
    ncr_table.batch_put_records(records)

    logger.info('Updated %s NCRs out of %s', ncr_updated_count, len(ncrs))
