from typing import Union, NamedTuple

from boto3.dynamodb.conditions import Attr, Key

from lib.dynamodb.table_base import TableBase


class NcrIdParts(NamedTuple):
    scan_id_date: str
    scan_id_randomness: str
    account_id: str
    resource_id: str
    requirement_id: str

    @property
    def scan_id(self):
        return f'{self.scan_id_date}#{self.scan_id_randomness}'

    @property
    def accntId_rsrceId_rqrmntId(self): # pylint: disable=invalid-name
        return NCRTable.create_sort_key(self.account_id, self.resource_id, self.requirement_id)


class NCRTable(TableBase):
    CLOUDSPLOIT_FINDING_NA = 'N/A'  # string in cloudsploit finding indicating no resource ID
    REMEDIATION_SUCCESS = 'Success'
    REMEDIATION_IN_PROGRESS = 'In Progress'
    REMEDIATION_ERROR = 'Error'

    def update_remediation_status(self, ncr: dict, status: str, check_remediation_started=True) -> Union[bool, dict]:
        """
        update ncr with a field 'remediated' with string value
        provided that this field does not already exist iff exists_check
        """
        kwargs = {
            'Key': {
                'scanId': ncr['scanId'],
                'accntId_rsrceId_rqrmntId': ncr['accntId_rsrceId_rqrmntId']
            },
            'UpdateExpression': 'SET remediated = :status',
            'ExpressionAttributeValues': {
                ':status': status
            },
            'ReturnValues': 'ALL_NEW'
        }
        if check_remediation_started:
            kwargs['ConditionExpression'] = Attr('remediated').not_exists() | Attr('remediated').eq(None)
        try:
            return self.update_item(**kwargs)
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            return False

    @staticmethod
    def create_ncr_id(ncr: dict) -> str:
        """NCR IDs uniquely identify an NCR, use so API only requires a single value"""
        return f'{ncr["scanId"]}#{ncr["accntId_rsrceId_rqrmntId"]}'

    @staticmethod
    def parse_ncr_id(ncr_id: str) -> NcrIdParts:
        return NcrIdParts._make(ncr_id.split('#'))

    def get_all_account_ncrs_by_requirement_id(self, scan_id: str, account_id: str, requirement_id: str) -> list:
        return self.query_all(
            IndexName='by-scanId',
            KeyConditionExpression=Key('scanId').eq(scan_id) & Key('rqrmntId_accntId').eq(f'{requirement_id}#{account_id}')
        )

    def get_all_account_ncrs(self, scan_id: str, account_id: str) -> list:
        return self.query_all(
            KeyConditionExpression=Key('scanId').eq(scan_id) & Key('accntId_rsrceId_rqrmntId').begins_with(account_id)
        )

    def get_ncr(self, scan_id: str, account_id: str, resource_id: str, requirement_id: str) -> dict:
        return self.get_item(
            Key={
                'scanId': scan_id,
                'accntId_rsrceId_rqrmntId': '#'.join([
                    account_id,
                    resource_id,
                    requirement_id,
                ]),
            }).get('Item', {})

    @staticmethod
    def create_sort_key(account_id, resource_id, requirement_id):
        return f'{account_id}#{resource_id}#{requirement_id}'

    @staticmethod
    def create_gsi_sort_key(account_id, requirement_id):
        return f'{requirement_id}#{account_id}'

    @staticmethod
    def new_ncr_record(data: dict, scan_id: str) -> dict:
        """
        :param data: dict containing k:v pairs representing ncr record
        :param scan_id: str with scan_id to use as pk for ncr table
        :return: ncr record (dict)
        """
        new_items = {
            'scanId': scan_id,
            'accntId_rsrceId_rqrmntId': NCRTable.create_sort_key(data['accountId'], data['resourceId'], data['requirementId']),
            'rqrmntId_accntId': NCRTable.create_gsi_sort_key(data['accountId'], data['requirementId']),
        }
        return {**data, **new_items}
