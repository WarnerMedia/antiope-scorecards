import random
from json import loads
from unittest.mock import patch

from api.account_detailed_scores import account_detailed_scores_handler
from lib.dynamodb import accounts_table, scans_table, scores_table, user_table

ACCOUNT_ID = str(random.randrange(500000, 999999))
ACCOUNT_ID2 = str(random.randrange(500000, 999999))
SCAN_ID = '101010abc'

EVENT = {
    'pathParameters': {
        'accountIds': ACCOUNT_ID+','+ACCOUNT_ID2
    },
    'requestContext': {
        'authorizer': {
            'claims': {
                'email': 'example2@gmail.com'
            }
        }
    }
}
TEST_ACCOUNTS = [
    {
        'accountId': ACCOUNT_ID,
        'account_name': 'Sample Text'
    },
    {
        'accountId': ACCOUNT_ID2,
        'account_name': 'Sample Text'
    }
]

TEST_SCORES = [
    {
        'accntId_rqrmntId': ACCOUNT_ID + '#303030',
        'requirementId': '303030',
        'accountId': ACCOUNT_ID,
        'date': '2020-05-03',
        'scanId': SCAN_ID,
        'accountName': 'Sample Text',
        'score': {
            'high': {
                'weight': 10,
                'numFailing': 10,
                'numResources': 10, }}},
    {
        'accntId_rqrmntId': ACCOUNT_ID + '#404040',
        'requirementId': '404040',
        'accountId': ACCOUNT_ID,
        'date': '2020-05-03',
        'scanId': SCAN_ID,
        'accountName': 'Sample Text',
        'score': {
            'low': {'weight': 10,
                    'numFailing': 10,
                    'numResources': 10, }}},
    {
        'accntId_rqrmntId': ACCOUNT_ID2 + '#303030',
        'requirementId': '303030',
        'accountId': ACCOUNT_ID2,
        'date': '2020-05-03',
        'scanId': SCAN_ID,
        'accountName': 'Sample Text',
        'score': {
            'critical': {
                'weight': 10,
                'numFailing': 10,
                'numResources': 10, }}},
]

DESIRED_OUTPUT = {
    'accounts':
        [
            {'accountId': ACCOUNT_ID,
             'accountName': 'Sample Text',
             'requirementsScores':
                 [{'requirementId': '303030',
                   'score':
                       {'high': {'weight': 10,
                                 'numFailing': 10,
                                 'numResources': 10, }}},
                  {'requirementId': '404040',
                   'score':
                       {'low': {'weight': 10,
                                'numFailing': 10,
                                'numResources': 10, }}}]},
            {'accountId': ACCOUNT_ID2,
             'accountName': 'Sample Text',
             'requirementsScores':
                 [{'requirementId': '303030',
                   'score':
                       {'critical': {'weight': 10,
                                     'numFailing': 10,
                                     'numResources': 10, }}}, ]}
        ],

    'scanId': SCAN_ID,
}


class TestAccountDetailedScores:
    @patch.object(accounts_table, 'get_account')
    @patch.object(user_table, 'get_user')
    @patch.object(scans_table, 'get_latest_complete_scan')
    def test_valid_event(self, mock_query_scans, mock_get_user, mock_get_account):
        mock_get_account.side_effect = TEST_ACCOUNTS
        mock_query_scans.return_value = SCAN_ID
        mock_get_user.return_value = {
            'accounts': {
                ACCOUNT_ID: {},
                ACCOUNT_ID2: {},
            },
        }
        scores_table.batch_put_records(TEST_SCORES)

        response = account_detailed_scores_handler(EVENT, None)
        assert response['statusCode'] == 200
        assert loads(response['body']) == DESIRED_OUTPUT

    def test_invalid_event(self):
        invalid_event = {**EVENT}
        del invalid_event['requestContext']
        response = account_detailed_scores_handler(invalid_event, None)
        assert response['statusCode'] == 400

    def test_bad_auth(self):
        invalid_event = {**EVENT}
        invalid_event['requestContext']['authorizer']['claims']['email'] = 'bad_email@gmail.com'
        response = account_detailed_scores_handler(invalid_event, None)
        assert response['statusCode'] == 403

    @patch.object(accounts_table, 'get_account')
    @patch.object(user_table, 'get_user')
    @patch.object(scans_table, 'get_latest_complete_scan')
    def test_admin_user(self, mock_query_scans, mock_get_user, mock_get_account):
        mock_get_account.side_effect = TEST_ACCOUNTS
        mock_query_scans.return_value = SCAN_ID
        mock_get_user.return_value = {
            'isAdmin': True,
        }

        response = account_detailed_scores_handler(EVENT, None)
        assert response['statusCode'] == 200
        assert loads(response['body']) == DESIRED_OUTPUT
