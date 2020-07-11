import json

from tests.stepfunction.step_function_runner import step_function_run
from tests.stepfunction.helpers import lambda_response, get_success_expected_calls

error = {
    'errorMessage': 'division by zero',
    'errorType': 'ZeroDivisionError',
    'stackTrace': ['"  File \\"/var/task/lambda_function.py\\", line 5, in lambda_handler\\n    return 1/0\\n"']
}

cs_populate_failure = get_success_expected_calls()
cs_populate_failure['CloudSploitPopulate'][0][0].update({ # inject the failure
    'error': True,
    'reply': error
})
# add the error handler call
cs_populate_failure['CloudSploitError'] = [
    {
        'expected': {**cs_populate_failure['CloudSploitSetup'][0][0]['expected'], **{
            'cloudsploitSetup': lambda_response(cs_populate_failure['CloudSploitSetup'][0][0]['reply']),
            'error': {
                'Error': error['errorType'],
                'Cause': json.dumps(error)
            }
        }},
        'reply': {}
    }
]

def test_cs_populate(step_function):
    expected_calls = cs_populate_failure
    results, execution_result = step_function_run(step_function, expected_calls)
    for r in results:
        print(r)
        assert r['expected'] == r['received'], f'{r["functionName"]}: {r.get("error")}'
    print(execution_result)
    assert execution_result['status'] == 'SUCCEEDED'
    for function_name, calls_remaining in expected_calls.items():
        assert calls_remaining == [], f'{function_name}: had expected calls that were not made'
    print(execution_result)
