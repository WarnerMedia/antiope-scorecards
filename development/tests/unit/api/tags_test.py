"""unit tests for app/api/tags.py"""
import json
from unittest.mock import MagicMock, patch

from api import tags
from lib.dynamodb import user_table


def get_event():
    return {
        'pathParameters': {
            'ncrId': '09-06-2020%23randomness123%23123456789%23eni-123%23200'
        },
        'requestContext': {
            'authorizer': {
                'claims': {
                    'email': 'test@test.com',
                },
            },
        },
    }


class TestTags:
    @patch.object(user_table, 'get_user')
    def test_get_tags_user(self, mock_get_user):
        tags.init_configuration_es = MagicMock()
        mock_get_user.return_value = {
            'isAdmin': False,
            'accounts': {
                '123456789': {}
            }
        }
        mocked_hit_object = MagicMock()
        mocked_hit_object.to_dict = MagicMock(return_value={
            'tags': {
                'key1': 'value1'
            }
        })
        tags.es_tag_query = MagicMock(return_value=[mocked_hit_object])
        response = tags.tags_handler(get_event(), None)
        response['body'] = json.loads(response['body'])
        assert response['body']['ncrTags']
        assert response['body']['ncrTags']['ncrId'] == '09-06-2020#randomness123#123456789#eni-123#200'
        assert response['body']['ncrTags']['tags'] == [
            {
                'name': 'key1',
                'value': 'value1'
            }
        ]

    @patch.object(user_table, 'get_user')
    def test_get_tags_not_user(self, mock_get_user):
        tags.init_configuration_es = MagicMock()
        mock_get_user.return_value = {}
        response = tags.tags_handler(get_event(), None)
        response['body'] = json.loads(response['body'])
        assert response['statusCode'] == 403

    @patch.object(user_table, 'get_user')
    def test_get_tags_admin(self, mock_get_user):
        tags.init_configuration_es = MagicMock()
        mock_get_user.return_value = {
            'isAdmin': True,
        }
        mocked_hit_object = MagicMock()
        mocked_hit_object.to_dict = MagicMock(return_value={
            'tags': {
                'key1': 'value1'
            }
        })
        tags.es_tag_query = MagicMock(return_value=[mocked_hit_object])
        response = tags.tags_handler(get_event(), None)
        response['body'] = json.loads(response['body'])
        assert response['body']['ncrTags']
        assert response['body']['ncrTags']['ncrId'] == '09-06-2020#randomness123#123456789#eni-123#200'
        assert response['body']['ncrTags']['tags'] == [
            {
                'name': 'key1',
                'value': 'value1'
            }
        ]

    @patch.object(user_table, 'get_user')
    def test_get_tags_missing_account(self, mock_get_user):
        tags.init_configuration_es = MagicMock()
        mock_get_user.return_value = {
            'isAdmin': False,
            'accounts': {
                'wrong_account_id': {}
            }
        }
        response = tags.tags_handler(get_event(), None)
        response['body'] = json.loads(response['body'])
        assert response['statusCode'] == 403

    @patch.object(user_table, 'get_user')
    def test_get_tags_invalid_ncr(self, mock_get_user):
        mock_get_user.return_value = {
            'isAdmin': False,
            'accounts': {}
        }
        event = get_event()
        event['pathParameters']['ncrId'] = 'invalid' # too few ncr id parts

        response = tags.tags_handler(event, None)
        assert response['statusCode'] == 400

        event['pathParameters']['ncrId'] = 'i%23n%23v%23a%23l%23i%23d%23d%23' # too many ncr id parts

        response = tags.tags_handler(event, None)
        assert response['statusCode'] == 400
