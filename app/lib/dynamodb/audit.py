from datetime import datetime, date

from lib.dynamodb.table_base import TableBase


class AuditTable(TableBase):
    REMEDIATION_STARTED = 'Remediation started'
    REMEDIATION_COMPLETED = 'Remediation completed'
    REMEDIATION_ERRORED = 'Remediation errored'
    REMEDIATION_INVALID_INPUT = 'Remediation aborted - invalid input'
    REMEDIATION_IAC_OVERRIDE = 'Remediation aborted - iac override required'
    PUT_EXCLUSION_USER = 'Put Exclusion - User'
    PUT_EXCLUSION_ADMIN = 'Put Exclusion - Admin'

    def put_audit_trail(self, user_email: str, action: str, params: dict) -> None:
        """
        adds audit trail record.
        """
        return self.put_item(
            Item={
                'year': str(date.today().year),
                'timestamp': datetime.now().isoformat(),
                'user': user_email,
                'action': action,
                'parameters': params
            },
            ReturnValues='NONE'
        )
