from boto3.dynamodb.conditions import Key
from lib.dynamodb.table_base import TableBase

class TestTableBase:
    def test_scan_all(self):
        table = TableBase('audit-table')
        for i in range(3):
            table.put_item(Item={'year': '1970', 'timestamp': '1970-' + str(i)})
        results = table.scan_all(Limit=1)
        assert len(results) >= 3
        for i in range(3):
            table.delete_item(Key={'year': '1970', 'timestamp': '1970-' + str(i)})

    def test_query_all(self):
        table = TableBase('audit-table')
        for i in range(3):
            table.put_item(Item={'year': '1971', 'timestamp': '1971-' + str(i)})
        results = table.query_all(KeyConditionExpression=Key('year').eq('1971'), Limit=1)
        assert len(results) >= 3
        for i in range(3):
            table.delete_item(Key={'year': '1971', 'timestamp': '1971-' + str(i)})
