"""
Base class for extending boto3's dynamodb Table resource functionality
"""
import os
import json
from datetime import datetime, timedelta

import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

from lib.logger import logger


class TableBase():
    def __init__(self, table_name, ttl=None):
        if os.getenv('IS_LOCAL', None):
            kwargs = {'endpoint_url': 'http://localhost:8000'}
        else:
            kwargs = {}
        self.ttl = ttl
        self.dynamodb = boto3.client('dynamodb', **kwargs)
        self.dynamodb_table = boto3.resource('dynamodb', **kwargs)
        self.table = self.dynamodb_table.Table(table_name)
        self.table_name = table_name

    def get_ttl(self):
        return int((datetime.now() + timedelta(days=self.ttl)).timestamp())

    @staticmethod
    def serialize(target: dict):
        logger.debug('Serializing %s', json.dumps(target, default=str))
        serialized = TypeSerializer().serialize(target)['M']
        logger.debug('Serialized %s', json.dumps(serialized, default=str))
        return serialized

    @staticmethod
    def deserialize(target: dict):
        logger.debug('Deserializing %s', json.dumps(target, default=str))
        deserialized = TypeDeserializer().deserialize({'M': target})
        logger.debug('Deserialized %s', json.dumps(deserialized, default=str))
        return deserialized

    def delete_item(self, *args, **kwargs):
        """Pass through to table method"""
        return self.table.delete_item(*args, **kwargs)

    def get_item(self, *args, **kwargs):
        """Pass through to table method"""
        return self.table.get_item(*args, **kwargs)

    def put_item(self, *args, **kwargs):
        """Pass through to table method"""
        if self.ttl and 'Item' in kwargs and 'ttl' not in kwargs['Item']:
            kwargs['Item']['ttl'] = self.get_ttl()
        return self.table.put_item(*args, **kwargs)

    def update_item(self, *args, **kwargs):
        """Pass through to table method"""
        return self.table.update_item(*args, **kwargs)

    def query(self, *args, **kwargs):
        """Pass through to table method"""
        return self.table.query(*args, **kwargs)

    def scan(self, *args, **kwargs):
        """Pass through to table method"""
        return self.table.scan(*args, **kwargs)

    def batch_writer(self, *args, **kwargs):
        """Pass through to table method"""
        return self.table.batch_writer(*args, **kwargs)

    def scan_all(self, **kwargs):
        """Scans all items of a table, calls successive pages if necessary"""
        scan_params = kwargs
        response = self.table.scan(**scan_params)
        items = response.get('Items') or []
        while 'LastEvaluatedKey' in response:
            scan_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = self.table.scan(**scan_params)
            items.extend(response.get('Items') or [])
        return items

    def query_all(self, **kwargs):
        """Query items of a table, calls successive pages if necessary"""
        query_parameters = kwargs
        response = self.table.query(**query_parameters)
        items = response.get('Items') or []
        while 'LastEvaluatedKey' in response:
            query_parameters['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = self.table.query(**query_parameters)
            items.extend(response.get('Items') or [])
        return items

    def batch_put_records(self, records: list) -> None:
        """
        Write records to table using batch_writer
        (25 writes per api call with automatic retries)

        :param records: list of validated ddb records to put to db
        :return: None
        """
        with self.table.batch_writer() as batch:
            for record in records:
                if self.ttl and 'ttl' not in record:
                    record['ttl'] = self.get_ttl()
                batch.put_item(Item=record)
