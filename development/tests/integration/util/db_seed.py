import os
import boto3

resource_prefix = os.getenv('RESOURCE_PREFIX')
stage = os.getenv('STAGE', 'dev')
dynamodb = boto3.resource('dynamodb')
user_table = dynamodb.Table(f'{resource_prefix}-{stage}-users-table')
account_table = dynamodb.Table(f'{resource_prefix}-{stage}-accounts-table')


def create_admin(email):
    admin_record = {
        'email': email,
        'isAdmin': True,
    }
    user_table.put_item(Item=admin_record)
    return admin_record


def create_user(email, accounts=None):
    accounts = accounts if accounts is not None else {}
    user_record = {
        'email': email,
        'accounts': accounts,
    }
    user_table.put_item(Item=user_record)
    return user_record


def delete_admin(email):
    user_table.delete_item(Key={'email': email})


def create_account(record):
    account_table.put_item(Item=record)
    return record


def delete_account(account_id):
    account_table.delete_item(Key={'accountId': account_id})
