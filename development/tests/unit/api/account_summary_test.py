import random
from json import loads
from unittest.mock import patch

from api.account_summary import account_summary_handler
from lib.dynamodb import account_scores_table, accounts_table, user_table
from lib.s3.s3_buckets import S3

ACCOUNT_ID = str(random.randrange(500000, 999999))
ACCOUNT_ID2 = str(random.randrange(500000, 999999))
PAYER_ID = 'pay_id01'

EVENT = {
    'pathParameters': {
        'accountIds': ACCOUNT_ID+','+ACCOUNT_ID2,
    },
    'requestContext': {
        'authorizer': {
            'claims': {
                'email': 'example2@gmail.com'
            }
        }
    }
}

TEST_ACCOUNTS = [{'accountId': ACCOUNT_ID, 'account_name': 'account-name', 'payer_id': PAYER_ID},
                 {'accountId': ACCOUNT_ID2, 'payer_id': PAYER_ID}]

TEST_SCORE = [{
    'accountId': ACCOUNT_ID,
    'date': '2020-06-01',
    'scanId': ACCOUNT_ID,
    'score': {
        'high': {
            'weight': 10,
            'numResources': 10,
            'numFailing': 10,
        }
    }
}, {
    'accountId': ACCOUNT_ID,
    'date': '2020-05-04',  # Test for Monday
    'scanId': ACCOUNT_ID,
    'score': {
        'critical': {
            'weight': 10,
            'numResources': 10,
            'numFailing': 10,
        }
    }
}, {
    'accountId': ACCOUNT_ID,
    'date': '2020-05-07',  # Test for Not A Monday
    'scanId': ACCOUNT_ID,
    'score': {
        'low': {
            'weight': 10,
            'numResources': 10,
            'numFailing': 10,
        }
    }
}, {
    'accountId': ACCOUNT_ID2,
    'date': '2020-05-07',  # Test for Not A Monday
    'scanId': ACCOUNT_ID2,
    'score': {
        'critical': {
            'weight': 5,
            'numResources': 5,
            'numFailing': 5,
        }
    }
}]

DESIRED_OUTPUT = {
    'accounts': [
        {
            'accountId': ACCOUNT_ID,
            'accountName': 'account-name',
            'historicalScores': [{
                'date': '2020-05-04',
                'score': 100
            }],
            'currentScore': 100,
            'criticalCount': 0,
            'spreadsheetDownload': {'url': 'url-example'}
        },
        {
            'accountId': ACCOUNT_ID2,
            'accountName': ACCOUNT_ID2,
            'historicalScores': [],
            'currentScore': 25,
            'criticalCount': 5,
            'spreadsheetDownload': {'url': 'url-example'}
        }
    ]
}

class TestAccountSummary:
    @patch.object(S3, 'generate_presigned_url')
    @patch.object(user_table, 'get_user')
    def test_valid_event(self, mock_get_user, mock_s3_genpresignedurl):
        accounts_table.batch_put_records(TEST_ACCOUNTS)
        account_scores_table.batch_put_records(TEST_SCORE)
        mock_get_user.return_value = {
            'accounts': {
                ACCOUNT_ID: {},
                ACCOUNT_ID2: {},
            },
        }
        mock_s3_genpresignedurl.return_value = 'url-example'

        response = account_summary_handler(EVENT, None)
        assert response['statusCode'] == 200
        assert loads(response['body']) == DESIRED_OUTPUT

    def test_invalid_event(self):
        invalid_event = {**EVENT}
        del invalid_event['requestContext']
        response = account_summary_handler(invalid_event, None)
        assert response['statusCode'] == 400

    def test_bad_auth(self):
        invalid_event = {**EVENT}
        invalid_event['requestContext']['authorizer']['claims']['email'] = 'bad_email@gmail.com'
        response = account_summary_handler(invalid_event, None)
        assert response['statusCode'] == 403

    @patch.object(S3, 'generate_presigned_url')
    @patch.object(user_table, 'get_user')
    def test_admin_user(self, mock_get_user, mock_s3_genpresignedurl):
        mock_get_user.return_value = {
            'isAdmin': True
        }
        mock_s3_genpresignedurl.return_value = 'url-example'

        response = account_summary_handler(EVENT, None)
        assert response['statusCode'] == 200
        assert loads(response['body']) == DESIRED_OUTPUT
