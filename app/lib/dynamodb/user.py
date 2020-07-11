from lib.dynamodb.table_base import TableBase


class UserTable(TableBase):
    def get_user(self, email):
        return self.get_item(Key={'email': email}).get('Item')
