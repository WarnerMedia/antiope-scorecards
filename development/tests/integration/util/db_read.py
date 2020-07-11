import os
import boto3

resource_prefix = os.getenv('RESOURCE_PREFIX')
stage = os.getenv('STAGE', 'dev')
dynamodb = boto3.resource('dynamodb')
requirements_table = dynamodb.Table(f'{resource_prefix}-{stage}-requirements-table')
ncr_table = dynamodb.Table(f'{resource_prefix}-{stage}-nonCompliantResources-table')
config_table = dynamodb.Table(f'{resource_prefix}-{stage}-config-table')


def scan_requirements():
    response = requirements_table.scan()
    return response['Items']


def get_config(config):
    config_from_dynamodb = config_table.get_item(Key={'configId': config})
    return config_from_dynamodb.get('Item', {}).get('config')

def scan_ncrs():
    response = ncr_table.scan()
    return response['Items']
