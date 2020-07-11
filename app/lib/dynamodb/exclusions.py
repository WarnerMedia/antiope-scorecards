import json

from typing import NamedTuple

from lib.logger import logger
from lib.lambda_decorator import exceptions
from lib.dynamodb.table_base import TableBase

# exclusion record looks like this
# {
#   "accountId": "003045886537", # admin mutable, only account ID or single star, must be valid account
#   "requirementId": "RequirementId01", # immutable, must be valid requirement ID
#   mutable by admin, must match existing NCR (look for ncr based on scanId (use scan_id_decorator), accountId, reqid, resid, update NCR item in db)
#   "resourceId": "arn:aws:blah:blah:blah",
#   "adminComments": "no it isn't", # admin mutable, anything
#   "expirationDate": "2021/05/31", # must be under maxDurationInDays, user update only if to INITIAL, mutable by admin
#   "formFields": { # user update only if to INITIAL, mutable by admin, must be set
#     "reason": "it's fine"
#   },
#   "type": "approval", # immutable
#   "status": "initial",
#   "hidesResources": False, # admin mutable, default False
#   "lastModifiedByAdmin": "Joel Admin",
#   "lastModifiedByUser": "Joel",
#   "lastStatusChangeDate": "2021/05/01",
#   "rqrmntId_rsrceRegex": "RequirementId01#arn:aws:blah:blah:blah",
#   "updateRequested": { # user add/update, admin delete
#     "expirationDate": "2021/05/31", # these are the only two updatable
#     "formFields": {
#       "reason": "the true reason"
#     }
#   }
# }

class ExclusionIdParts(NamedTuple):
    account_id: str
    requirement_id: str
    resource_id: str


class ExclusionsTable(TableBase):
    @staticmethod
    def get_exclusion_id(exclusion: dict) -> str:
        return '#'.join([exclusion.get('accountId', ''), exclusion.get('requirementId', ''), exclusion.get('resourceId', '')])

    @staticmethod
    def parse_exclusion_id(exclusion_id: str) -> ExclusionIdParts:
        return ExclusionIdParts._make(exclusion_id.split('#'))

    def get_exclusion(self, **kwargs):
        """Get an exclusion from the database"""
        if 'exclusion_id' in kwargs:
            exclusion_id = kwargs['exclusion_id']
            parts = exclusion_id.split('#')
            if len(parts) != 3:
                logger.debug('Exclusion ID does not have 3 parts: %s', exclusion_id)
            account_id, requirement_id, resource_id = parts
        elif {'account_id', 'requirement_id', 'resource_id'} == set(kwargs.keys()):
            account_id = kwargs['account_id']
            requirement_id = kwargs['requirement_id']
            resource_id = kwargs['resource_id']
        else:
            logger.debug('Invalid get_exclusion arguments, must either supply exclusion_id or account_id, requirement_id, and resource_id')
            raise exceptions.HttpServerErrorException('Internal server error')
        exclusion = self.get_item(
            Key={
                'accountId': account_id,
                'rqrmntId_rsrceRegex': '#'.join([requirement_id, resource_id]),
            },
        ).get('Item', {})
        return exclusion

    def update_exclusion(self, new_exclusion, delete_exclusion=None):
        """Update an exclusion so long as the exclusion has all required keys"""
        logger.debug('New exclusion: %s', json.dumps(new_exclusion, default=str))
        logger.debug('Delete exclusion: %s', json.dumps(delete_exclusion, default=str))
        transaction_items = []
        if new_exclusion:
            transaction_items.append({
                'Put': {
                    'TableName': self.table_name,
                    'Item': self.serialize(new_exclusion),
                },
            })
        if delete_exclusion:
            transaction_items.append({
                'Delete': {
                    'TableName': self.table_name,
                    'Key': self.serialize({
                        'accountId': delete_exclusion['accountId'],
                        'rqrmntId_rsrceRegex': delete_exclusion['rqrmntId_rsrceRegex'],
                    }),
                },
            })
        logger.debug('Transaction items: %s', json.dumps(transaction_items, default=str))
        try:
            self.dynamodb.transact_write_items(TransactItems=transaction_items)
        except self.dynamodb.exceptions.TransactionCanceledException as err:
            logger.debug('Error making dynamodb transaction: %s', json.dumps(err.response, default=str))
            raise exceptions.HttpServerErrorException('Internal server error')
