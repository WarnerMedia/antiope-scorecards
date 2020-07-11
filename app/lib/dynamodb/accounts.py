from lib.dynamodb.table_base import TableBase


class AccountsTable(TableBase):
    def get_account(self, account_id):
        return self.get_item(
            Key={'accountId': account_id}
        )['Item']


    @staticmethod
    def normalize_account_record(account: dict):
        """
        Updates account record from account import file
        Mutates account dictionary
        """

        # consider just converting all snake_case/PascalCase to camelCase
        account['accountId'] = account['account_id']
