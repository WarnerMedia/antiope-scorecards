"""file concerned with implementation of GET /ncr/{ncrId}/tags endpoint"""
import os
import urllib.parse
import json

import boto3
from elasticsearch6 import RequestsHttpConnection
from elasticsearch6_dsl import Search, connections
from elasticsearch6_dsl.query import Bool
from requests_aws4auth import AWS4Auth

from lib import authz
from lib.logger import logger
from lib.dynamodb import ncr_table
from lib.lambda_decorator.decorator import api_decorator
from lib.lambda_decorator.email_decorator import email_decorator
from lib.lambda_decorator.exceptions import HttpInvalidException

def init_configuration_es():
    """creates connection needed to query the ElasticSearch cluster."""
    host = os.getenv('ES_ENDPOINT')
    region = os.getenv('ES_REGION')
    if not host.startswith('http'):
        host = 'https://' + host

    service = 'es'
    credentials = boto3.Session().get_credentials()
    aws_auth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service,
                        session_token=credentials.token)

    connections.create_connection(  # all operations will use this connection automatically.
        hosts=[host],
        http_auth=aws_auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )


def es_tag_query(account_id, resource_id):
    """Retrieves information pertaining to 1 particular resource with matching
    awsAccountId and resourceId values."""
    tag_query = Bool(
        must=[
            {
                'match': {
                    'awsAccountId': {
                        'query': account_id,
                        'operator': 'and'
                    }
                }
            },
            {
                'match': {
                    'resourceId': {
                        'query': resource_id,
                        'operator': 'and'
                    }
                }
            }
        ]
    )
    search_object = Search().query(tag_query)
    return search_object.execute()


def parse_es_tag_results(response):
    """Parses results of es_tag_query such that a list of dicts is returned"""
    to_return = []
    for hit in response:
        if tags := hit.to_dict().get('tags'):
            for key, value in tags.items():
                to_return.append({'name': key, 'value': value})
    return to_return


@email_decorator
@api_decorator
def tags_handler(event, context):
    """entry-point for Lambda function."""
    ncr_id = urllib.parse.unquote(event['pathParameters']['ncrId'])
    try:
        ncr_id_parts = ncr_table.parse_ncr_id(ncr_id)
    except TypeError:
        raise HttpInvalidException('invalid NCR ID')

    _, _, account_id, resource_id, _ = ncr_id_parts

    # authorization check
    authz.require_can_read_account(event['userRecord'], [account_id])

    init_configuration_es()  # establish connection to ElasticSearch cluster

    results = es_tag_query(account_id, resource_id)
    logger.debug('ES query results: %s', json.dumps(results, default=str))
    parsed_results = parse_es_tag_results(results)
    logger.debug('Parsed results: %s', json.dumps(parsed_results, default=str))

    response = {
        'ncrTags': {
            'ncrId': ncr_id,
            'tags': parsed_results
        }
    }

    return response
