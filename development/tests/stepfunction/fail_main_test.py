import json

from tests.stepfunction.step_function_runner import step_function_run

account_ids = ['1', '2', '3', '4', '5', '6']
s3_requirements_ids = ['req1', 'req2', 'req3']
scan_id = '2020/04/20T12:00:00.123#qwerasdf'

# Generic lambda error for many failures
error = {
    'errorMessage': 'division by zero',
    'errorType': 'ZeroDivisionError',
    'stackTrace': ['"  File \\"/var/task/lambda_function.py\\", line 5, in lambda_handler\\n    return 1/0\\n"']
}
load_failure = {
    'OpenScan': [{
        'expected': {},
        'reply': {'scanId': scan_id}
    }],
    'Load': [{
        'expected': {
            'openScan': {'scanId': scan_id},
        },
        'reply': error,
        'error': True
    }],
    'ScanError': [
        {
            'expected': {
                'openScan': {'scanId': scan_id},
                'scanError': {
                    'Error': error['errorType'],
                    'Cause': json.dumps(error)
                }
            },
            'reply': {'accountIds': account_ids, 's3RequirementIds': s3_requirements_ids}
        }
    ]
}


def test_fail_main(step_function):
    expected_calls = load_failure
    results, execution_result = step_function_run(step_function, expected_calls)
    for r in results:
        print(r)
        assert r['expected'] == r['received'], f'{r["functionName"]}: {r.get("error")}'
    print(execution_result)
    assert execution_result['status'] == 'FAILED'
    for function_name, calls_remaining in expected_calls.items():
        assert calls_remaining == [], f'{function_name}: had expected calls that were not made'
    print(execution_result)
