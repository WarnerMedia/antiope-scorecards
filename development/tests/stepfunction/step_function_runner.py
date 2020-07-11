import time

import boto3

from tests.stepfunction import lambda_stubber
# from step_function_tests import tests
# Assumes:
# Step function local is running at http://localhost:8083
# Step function local is configured to use lambda endpoint http://localhost:9000
# Step function is created in local step function
# Step function arn is 'arn:aws:states:us-east-1:123456789012:stateMachine:main'

STEP_FUNCTION_URL = 'http://localhost:8083'
states = boto3.client('stepfunctions', endpoint_url=STEP_FUNCTION_URL)


def step_function_run(step_function_arn, expected_calls):
    lambda_stubber.start_lambda_stubs('localhost', 9000, expected_calls)
    time.sleep(.25)
    response = states.start_execution(
        stateMachineArn=step_function_arn,
        input='{}'
    )
    execution_arn = response['executionArn']
    while (execution_result := states.describe_execution(executionArn=execution_arn))['status'] == 'RUNNING':
        time.sleep(.25)
    results = lambda_stubber.get_results()
    time.sleep(.1) # let things settle
    return results, execution_result
