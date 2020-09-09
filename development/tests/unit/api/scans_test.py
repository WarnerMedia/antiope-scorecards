import json

from unittest.mock import patch

from api import scans
from lib.dynamodb import scans_table
from tests.unit.api.test_setup_resources.sample_records import SCAN_DATA


class TestScans:
    def test_determine_bytes_us_ascii(self):
        string = 'one,two'
        result = scans.determine_bytes(string)
        assert result == 7

    def test_determine_bytes_mathematical_symbol(self):
        """the intention here is to ensure that bytes value is being determined rather than simply
        the length of the string."""
        string = '∀'
        result = scans.determine_bytes(string)
        assert result == 3

    def test_make_result(self):
        records = [SCAN_DATA[0]]
        result = scans.make_result(records)
        assert result == {'scans': records}

    def test_make_max_return(self):
        record = SCAN_DATA[0]
        records = [record for _ in range(100)]
        result = scans.make_max_return(records, 350)
        assert result == {'scans': [record for _ in range(2)]}

    @patch.object(scans_table, 'query_all')
    def test_scans_handler(self, mock_query_all):
        mock_query_all.return_value = SCAN_DATA
        result = scans.scans_handler({}, {})

        assert result['statusCode'] == 200
        assert json.loads(result['body'])['scans'] == SCAN_DATA
