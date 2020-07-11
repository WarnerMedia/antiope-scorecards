from tests.stepfunction.step_function_runner import step_function_run
from tests.stepfunction.helpers import get_success_expected_calls

def test_success(step_function):
    expected_calls = get_success_expected_calls()
    results, execution_result = step_function_run(step_function, expected_calls)
    for r in results:
        print(r)
        assert r['expected'] == r['received'], f'{r["functionName"]}: {r.get("error")}'
    print(execution_result)
    assert execution_result['status'] == 'SUCCEEDED'
    for function_name, calls_remaining in expected_calls.items():
        assert calls_remaining == [], f'{function_name}: had expected calls that were not made'
