import json

from tests.stepfunction.step_function_runner import step_function_run
from tests.stepfunction.helpers import get_success_expected_calls

error = {
    'errorMessage': 'division by zero',
    'errorType': 'ZeroDivisionError',
    'stackTrace': ['"  File \\"/var/task/lambda_function.py\\", line 5, in lambda_handler\\n    return 1/0\\n"']
}

global_spreadsheet_failure = get_success_expected_calls()
global_spreadsheet_failure['GenerateSpreadsheets'][0][0].update({ # inject the failure
    'error': True,
    'reply': error
})
# add the error handler call
global_spreadsheet_failure['GenerateSpreadsheetsError'] = [
    {
        'expected': {
            'openScan': global_spreadsheet_failure['Exclude'][0]['expected']['openScan'],
            'load': global_spreadsheet_failure['Exclude'][0]['expected']['load'],
            'error': {
                'Error': error['errorType'],
                'Cause': json.dumps(error)
            },
        },
        'reply': {}
    }
]

global_spreadsheet_failure['sqsSendMessage'] = [
    {
        'expected': None, # we don't bother parsing this
        'reply': {
            # the MD5CheckSum will need to be updated if the input to this is updated.
            'body': '<?xml version="1.0"?><SendMessageResponse xmlns="http://queue.amazonaws.com/doc/2012-11-05/"><SendMessageResult><MessageId>a66d2f5e-ab78-470c-af88-da07d054f555</MessageId><MD5OfMessageBody>e04a5d2ac10c83336af513e63c69e096</MD5OfMessageBody></SendMessageResult><ResponseMetadata><RequestId>cc36d4a2-5416-5826-9179-83f3b4e96ffa</RequestId></ResponseMetadata></SendMessageResponse>', # pylint: disable=line-too-long
            'content-type': 'text/xml'
        }
    }
]

def test_fail_global_spreadsheet(step_function):
    expected_calls = global_spreadsheet_failure
    results, execution_result = step_function_run(step_function, expected_calls)
    for r in results:
        print(r)
        assert r['expected'] == r['received'], f'{r["functionName"]}: {r.get("error")}'
    print(execution_result)
    assert execution_result['status'] == 'SUCCEEDED'
    for function_name, calls_remaining in expected_calls.items():
        assert calls_remaining == [], f'{function_name}: had expected calls that were not made'
