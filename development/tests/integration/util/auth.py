import os
import secrets
import uuid

import boto3
import warrant

ssm = boto3.client('ssm')
cognito = boto3.client('cognito-idp')

resource_prefix = os.getenv('RESOURCE_PREFIX')
stage = os.getenv('STAGE', 'dev')

app_client_id = ssm.get_parameter(Name=f'/{resource_prefix}/{stage}/auth/app-client-id')['Parameter']['Value']
user_pool_id = ssm.get_parameter(Name=f'/{resource_prefix}/{stage}/auth/user-pool-id')['Parameter']['Value']

test_identifier = uuid.uuid4()
credentials = {
    'admin': {
        'username': 'integration-test+{}-admin@test.com'.format(test_identifier),
        'password': 'Ab1!' + secrets.token_urlsafe(20),
    },
    'user': {
        'username': 'integration-test+{}-user@test.com'.format(test_identifier),
        'password': 'Ab1!' + secrets.token_urlsafe(20),
    },
    'not_authenticated': {
        'username': 'integration-test+{}-not_authenticated@test.com'.format(test_identifier),
        'password': 'Ab1!' + secrets.token_urlsafe(20),
    },
}


def get_jwt(user_credentials):
    user = warrant.Cognito(user_pool_id, app_client_id, username=user_credentials['username'])
    user.authenticate(password=user_credentials['password'])
    return user.id_token


def create_user(user_credentials):
    cognito.sign_up(
        Username=user_credentials['username'],
        Password=user_credentials['password'],
        ClientId=app_client_id,
    )
    cognito.admin_confirm_sign_up(
        UserPoolId=user_pool_id,
        Username=user_credentials['username'],
    )


def delete_user(user_credentials):
    cognito.admin_delete_user(
        UserPoolId=user_pool_id,
        Username=user_credentials['username'],
    )
