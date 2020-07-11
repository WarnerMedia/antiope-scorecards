import json
from lib.dynamodb import scans_table

class TestScanHandler:
    def test_add_error(self):
        scan_id = scans_table.create_new_scan_id()

        function_name = 'functionName'
        error1 = 'error1'
        error2 = 'error2'
        error3 = 'error3'
        error4 = {
            'Cause': json.dumps({
                'errorMessage': 'An error occurred (AccessDenied)',
                'errorType':'SampleError'
            }),
            'Error': 'SampleError'
        }

        scan_key = {'scan': scans_table.SCAN, 'scanId': scan_id}

        scans_table.put_item(
            Item={
                'scan': scans_table.SCAN,
                'processState': scans_table.IN_PROGRESS,
                'scanId': scan_id,
            }
        )

        # test adding error when none previously exist
        expected_result = {
            'scan': scans_table.SCAN,
            'processState': scans_table.IN_PROGRESS,
            'scanId': scan_id,
            'errors': [
                {
                    'functionName': function_name,
                    'error': error1
                }
            ]
        }

        scans_table.add_error(scan_id, function_name, error1)
        result = scans_table.get_item(Key=scan_key)['Item']
        assert result.pop('ttl')
        assert result == expected_result

        # test adding error when error previously exists
        expected_result = {
            'scan': scans_table.SCAN,
            'processState': scans_table.IN_PROGRESS,
            'scanId': scan_id,
            'errors': [
                {
                    'functionName': function_name,
                    'error': error1
                },
                {
                    'functionName': function_name,
                    'error': error2
                }
            ]
        }

        scans_table.add_error(scan_id, function_name, error2)
        result = scans_table.get_item(Key=scan_key)['Item']
        assert result.pop('ttl')
        assert result == expected_result

        # test adding fatal error
        expected_result = {
            'scan': scans_table.SCAN,
            'processState': scans_table.ERRORED,
            'scanId': scan_id,
            'errors': [
                {
                    'functionName': function_name,
                    'error': error1
                },
                {
                    'functionName': function_name,
                    'error': error2
                }
            ],
            'fatalError' :{
                'functionName': function_name,
                'error': error3
            }
        }

        scans_table.add_error(scan_id, function_name, error3, is_fatal=True)
        result = scans_table.get_item(Key=scan_key)['Item']
        assert result.pop('ttl')
        assert result == expected_result

        #test JSON parsing a step function error
        expected_result = {
            'scan': scans_table.SCAN,
            'processState': scans_table.ERRORED,
            'scanId': scan_id,
            'errors': [
                {
                    'error': 'error1',
                    'functionName': 'functionName'
                },
                {
                    'error': 'error2',
                    'functionName': 'functionName'
                },
                {
                    'error': {
                        'Error': 'SampleError',
                        'Cause': {
                            'errorMessage': 'An error occurred (AccessDenied)',
                            'errorType': 'SampleError'
                            }},
                    'functionName': 'functionName'}
                ],
            'fatalError':
                {
                    'error': 'error3',
                    'functionName': 'functionName'
                }
            }

        scans_table.add_error(scan_id, function_name, error4, is_fatal=False)
        result = scans_table.get_item(Key=scan_key)['Item']
        assert result.pop('ttl')
        assert result == expected_result
