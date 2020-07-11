#!/usr/bin/env python3

import argparse
import os
import sys

import boto3
import warrant

# writes a congito jwt to stdout for the provided user
def main(args):
    ssm = boto3.client('ssm')

    app_client_id = ssm.get_parameter(Name=f'/{args.resource_prefix}/{args.stage}/auth/app-client-id')['Parameter']['Value']
    user_pool_id = ssm.get_parameter(Name=f'/{args.resource_prefix}/{args.stage}/auth/user-pool-id')['Parameter']['Value']
    user = warrant.Cognito(user_pool_id, app_client_id, username=args.username)
    user.authenticate(password=args.password)
    print(user.id_token, end='')

def do_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--resource-prefix', help='resource prefix', required=False, default='antiope-scorecards')
    parser.add_argument('--stage', help='stage name to get credentials for', required=True)
    parser.add_argument('--username', help='username to get credentials for', required=True)
    parser.add_argument('--password', help='user\'s password', required=True)

    args = parser.parse_args()
    return(args)

if __name__ == '__main__':
    args = do_args()
    main(args)
