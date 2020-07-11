from datetime import datetime
import json
import random
import string

from boto3.dynamodb.conditions import Attr, Key

from lib.dynamodb.table_base import TableBase

class ScansTable(TableBase):
    SCAN = 'scan'
    COMPLETED = 'Completed'
    IN_PROGRESS = 'In Progress'
    ERRORED = 'Errored'

    @staticmethod
    def create_new_scan_id() -> str:
        random_length = 8
        scan_id = '{}#{}'.format(
            datetime.now().isoformat(),
            ''.join((random.choice(string.ascii_lowercase) for i in range(random_length))),
        )
        return scan_id

    def get_latest_complete_scan(self):
        # get last scan id from database
        scans = self.query_all(
            KeyConditionExpression=Key('scan').eq(self.SCAN),
            ScanIndexForward=False,
            FilterExpression=Attr('processState').eq(self.COMPLETED),
        )
        try:
            scan_id = scans[0]['scanId']
        except IndexError:
            scan_id = None

        return scan_id

    def add_error(self, scan_id, function_name, error, is_fatal=False):
        error_info = {
            'functionName': function_name,
            'error': error
        }

        # json parse the error Cause attribute (if we can)
        try:
            error['Cause'] = json.loads(error['Cause'])
        except: # pylint: disable=bare-except
            pass

        if is_fatal is True:
            self.update_item(
                Key={'scan': self.SCAN, 'scanId': scan_id},
                UpdateExpression='SET fatalError = :error_info, processState = :process_state',
                ExpressionAttributeValues={
                    ':error_info': error_info,
                    ':process_state': self.ERRORED
                },
                ReturnValues='NONE',
            )
        else:
            self.update_item(
                Key={'scan': self.SCAN, 'scanId': scan_id},
                UpdateExpression='SET errors = list_append(if_not_exists(errors, :empty_list), :error_info)',
                ExpressionAttributeValues={
                    ':error_info':[error_info],
                    ':empty_list': [],
                },
                ReturnValues='NONE',
            )
