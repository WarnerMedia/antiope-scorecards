import hashlib
import json

import boto3
import pytest

STEP_FUNCTION_URL = 'http://localhost:8083'

def lambda_arn(name: str) -> str:
    return f'arn:aws:lambda:us-east-1:012345678901:function:{name}'

@pytest.fixture(scope='session')
def step_function():
    # create the step function in the local step function instance
    # returns the arn of the step function
    with open('templates/stepfunction.asl.json') as file:
        step_function_definition = file.read()

    with open('templates/cloudsploit-iterator.asl.json') as file:
        cs_iterator_definition = file.read()
    # Using the hash of the definition lets us not worry about deleting old versions

    step_function_name = 'sf-main-' + hashlib.md5(step_function_definition.encode('utf-8')).hexdigest()
    cs_iterator_name = 'sf-cs-' + hashlib.md5(cs_iterator_definition.encode('utf-8')).hexdigest()

    cs_iterator_definition_parsed = json.loads(cs_iterator_definition)
    step_function_definition_parsed = json.loads(step_function_definition)

    # fix resource arns
    cs_iterator_definition_parsed['States']\
        ['IterateCloudSploitAccounts']['Iterator']['States']\
        ['CloudSploitSetup']['Resource'] = lambda_arn('CloudSploitSetup')
    cs_iterator_definition_parsed['States']\
        ['IterateCloudSploitAccounts']['Iterator']['States']\
        ['CloudSploitPopulate']['Resource'] = lambda_arn('CloudSploitPopulate')
    cs_iterator_definition_parsed['States']\
        ['IterateCloudSploitAccounts']['Iterator']['States']\
        ['CloudSploitError']['Resource'] = lambda_arn('CloudSploitError')

    step_function_definition_parsed['States']\
        ['OpenScan']['Resource'] = lambda_arn('OpenScan')
    step_function_definition_parsed['States']\
        ['LoadStaticData']['Resource'] = lambda_arn('Load')
    step_function_definition_parsed['States']\
        ['ParallelLoading']['Branches'][1]['States']\
        ['IterateS3Imports']['Iterator']['States']\
        ['S3Import']['Resource'] = lambda_arn('S3Import')
    step_function_definition_parsed['States']\
        ['ParallelLoading']['Branches'][1]['States']\
        ['IterateS3Imports']['Iterator']['States']\
        ['S3ImportError']['Resource'] = lambda_arn('S3ImportError')
    step_function_definition_parsed['States']\
        ['Exclude']['Resource'] = lambda_arn('Exclude')
    step_function_definition_parsed['States']\
        ['ScoreCalculate']['Resource'] = lambda_arn('ScoreCalculations')
    step_function_definition_parsed['States']\
        ['ParallelSpreadsheets']['Branches'][0]['States']\
        ['IterateAccountSpreadsheets']['Iterator']['States']\
        ['AccountSpreadsheets']['Resource'] = lambda_arn('GenerateSpreadsheets')
    step_function_definition_parsed['States']\
        ['ParallelSpreadsheets']['Branches'][0]['States']\
        ['IterateAccountSpreadsheets']['Iterator']['States']\
        ['AccountSpreadsheetsError']['Resource'] = lambda_arn('GenerateSpreadsheetsError')
    step_function_definition_parsed['States']\
        ['ParallelSpreadsheets']['Branches'][1]['States']\
        ['SetupUserSpreadsheets']['Resource'] = lambda_arn('SetupUserSpreadsheets')
    step_function_definition_parsed['States']\
        ['ParallelSpreadsheets']['Branches'][1]['States']\
        ['IterateUserSpreadsheets']['Iterator']['States']\
        ['UserSpreadsheets']['Resource'] = lambda_arn('GenerateSpreadsheets')
    step_function_definition_parsed['States']\
        ['ParallelSpreadsheets']['Branches'][1]['States']\
        ['IterateUserSpreadsheets']['Iterator']['States']\
        ['UserSpreadsheetsError']['Resource'] = lambda_arn('GenerateSpreadsheetsError')
    step_function_definition_parsed['States']\
        ['ParallelSpreadsheets']['Branches'][2]['States']\
        ['IteratePayerSpreadsheets']['Iterator']['States']\
        ['PayerSpreadsheets']['Resource'] = lambda_arn('GenerateSpreadsheets')
    step_function_definition_parsed['States']\
        ['ParallelSpreadsheets']['Branches'][2]['States']\
        ['IteratePayerSpreadsheets']['Iterator']['States']\
        ['PayerSpreadsheetsError']['Resource'] = lambda_arn('GenerateSpreadsheetsError')
    step_function_definition_parsed['States']\
        ['ParallelSpreadsheets']['Branches'][3]['States']\
        ['GlobalSpreadsheet']['Resource'] = lambda_arn('GenerateSpreadsheets')
    step_function_definition_parsed['States']\
        ['ParallelSpreadsheets']['Branches'][3]['States']\
        ['GlobalSpreadsheetError']['Resource'] = lambda_arn('GenerateSpreadsheetsError')
    step_function_definition_parsed['States']\
        ['CloseScan']['Resource'] = lambda_arn('CloseScan')
    step_function_definition_parsed['States']\
        ['Error']['Resource'] = lambda_arn('ScanError')

    # fix the cs_iterator step function arnc
    step_function_definition_parsed['States']['ParallelLoading']\
        ['Branches'][0]['States']['CloudSploitSubStepFunction']\
            ['Parameters']['StateMachineArn'] = 'arn:aws:states:us-east-1:123456789012:stateMachine:' + cs_iterator_name
    step_function_definition_parsed['States']['ParallelLoading']\
        ['Branches'][0]['States']['CloudSploitSubStepFunction']\
            ['Resource'] = 'arn:aws:states:::states:startExecution.sync'

    # convert sqs queue url to a lambda url
    step_function_definition_parsed['States']['ParallelSpreadsheets']\
        ['Branches'][3]['States']['GlobalSpreadsheetErrorEnqueue']\
            ['Parameters']['QueueUrl'] = 'http://localhost:9000/x/y/sqsSendMessage'

    step_function_definition = json.dumps(step_function_definition_parsed)
    cs_iterator_definition = json.dumps(cs_iterator_definition_parsed)

    step_functions = boto3.client('stepfunctions', endpoint_url=STEP_FUNCTION_URL)

    step_functions.create_state_machine(
        definition=cs_iterator_definition,
        name=cs_iterator_name,
        roleArn='arn:aws:iam::012345678901:role/DummyRole'
    )

    results = step_functions.create_state_machine(
        definition=step_function_definition,
        name=step_function_name,
        roleArn='arn:aws:iam::012345678901:role/DummyRole'
    )
    return results['stateMachineArn']
