from datetime import date
from boto3.dynamodb.conditions import Key
from lib.dynamodb import audit_table


class TestAuditTable:
    def test_put_audit_trail(self):
        email = 'sample@sample.com'
        action = audit_table.REMEDIATION_STARTED
        params = {'foo': 'bar'}

        audit_table.put_audit_trail(email, action, params)
        result = audit_table.query(
            KeyConditionExpression=Key('year').eq(str(date.today().year)),
            ScanIndexForward=False
        ).get('Items', [])[0]

        assert result.get('user') == email
        assert result.get('action') == audit_table.REMEDIATION_STARTED
        assert result.get('parameters') == params
        assert result.get('year') == str(date.today().year)
