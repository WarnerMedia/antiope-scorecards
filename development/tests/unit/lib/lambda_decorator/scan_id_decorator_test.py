import pytest

from lib.dynamodb import scans_table
from lib.lambda_decorator.scan_id_decorator import get_scan_id_decorator


@pytest.fixture(scope='function')
def dummy_data():
    scans_table.put_item(Item={'scan': scans_table.SCAN, 'processState': scans_table.COMPLETED, 'scanId': '3030-scantest'})
    scans_table.put_item(Item={'scan': scans_table.SCAN, 'processState': scans_table.IN_PROGRESS, 'scanId': '4030-scantest'})
    yield
    scans_table.delete_item(Key={'scan': scans_table.SCAN, 'scanId': '3030-scantest'})
    scans_table.delete_item(Key={'scan': scans_table.SCAN, 'scanId': '4030-scantest'})


def test_scan_happy(dummy_data):
    @get_scan_id_decorator
    def dummy_lambda_handler(event, context):
        assert event['scanId'] == '3030-scantest'
        return {'pass': 'yes'}

    test_scan = dummy_lambda_handler({}, {})
    assert set(test_scan.keys()) == {'pass', 'scanId'}
    assert test_scan == {'pass': 'yes', 'scanId': '3030-scantest'}
