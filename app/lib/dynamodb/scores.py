import numbers
from typing import TypedDict, Optional
from collections import defaultdict

from lib.dynamodb.table_base import TableBase

class DetailedScore(TypedDict):
    scanId: str
    accountId: str
    requirementId: str
    score: dict
    accntId_rqrmntId: Optional[str]


class ScoresTable(TableBase):
    DATA_NOT_COLLECTED = 'DNC'  # in the event that data is not collected, score = DATA_NOT_COLLECTED
    NOT_APPLICABLE = 'N/A' # score for requirements that do not apply to an account

    @staticmethod
    def new_score(scan_id, account_id, requirement, num_resources, num_failing=None) -> DetailedScore:
        return {
            'scanId': scan_id,
            'accntId_rqrmntId': f'{account_id}#{requirement["requirementId"]}',
            'accountId': account_id,
            'requirementId': requirement['requirementId'],
            'score': {
                requirement['severity']: {
                    'weight': requirement['weight'],
                    'numResources': num_resources,
                    'numFailing': num_failing,
                }
            }
        }

    @staticmethod
    def new_empty_score_object():
        return {
            'numFailing': 0,
            'numResources': 0,
            'weight': 0
        }

    @classmethod
    def get_single_score_calc(cls, aggregated_score: dict) -> int:
        single_score = 0
        for score in aggregated_score.values():
            single_score += score['numFailing']*score['weight']

        return single_score

    @classmethod
    def weighted_score_aggregate_calc(cls, score_objects: list) -> dict:
        aggregate_score_object: dict = defaultdict(cls.new_empty_score_object)
        for score in score_objects:
            for severity, data in score['score'].items():
                if isinstance(data['numFailing'], numbers.Number) and isinstance(data['numResources'], numbers.Number):
                    aggregate_score_object[severity]['weight'] = data['weight']
                    aggregate_score_object[severity]['numFailing'] += data['numFailing']
                    aggregate_score_object[severity]['numResources'] += data['numResources']

        return aggregate_score_object
