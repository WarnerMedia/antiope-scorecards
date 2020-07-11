from lib.dynamodb import ncr_table


class TestNcrTable:
    def test_update_remediation_status(self):
        existing_ncr = {
            'scanId': '111',
            'accntId_rsrceId_rqrmntId': 'aaa#bbb#ccc'
        }
        ncr_table.put_item(Item=existing_ncr)
        results = ncr_table.update_remediation_status(existing_ncr, ncr_table.REMEDIATION_SUCCESS)
        assert results is not False

    def test_error_update_remediation_status(self):
        existing_ncr = {
            'scanId': '222',
            'accntId_rsrceId_rqrmntId': 'xxx#yyy#zzz',
            'remediated': True
        }
        ncr_table.put_item(Item=existing_ncr)
        results = ncr_table.update_remediation_status(existing_ncr, ncr_table.REMEDIATION_SUCCESS)
        assert results is False

    def test_error_update_remediation_status_none(self):
        existing_ncr = {
            'scanId': '222',
            'accntId_rsrceId_rqrmntId': 'xxx#yyy#zzz',
            'remediated': None
        }
        ncr_table.put_item(Item=existing_ncr)
        results = ncr_table.update_remediation_status(existing_ncr, ncr_table.REMEDIATION_SUCCESS)
        assert results is not False

    def test_sort_key_creation(self):
        assert ncr_table.create_sort_key('aaa', 'bbb', 'ccc') == 'aaa#bbb#ccc'

    def test_ncr_record_creation(self):
        assert ncr_table.new_ncr_record({
            'accountId': 'bbb',
            'requirementId': 'ccc',
            'resourceId': 'ddd'
        }, 'sample') == {
            'scanId': 'sample',
            'accountId': 'bbb',
            'requirementId': 'ccc',
            'resourceId': 'ddd',
            'accntId_rsrceId_rqrmntId': 'bbb#ddd#ccc',
            'rqrmntId_accntId': 'ccc#bbb'
        }
