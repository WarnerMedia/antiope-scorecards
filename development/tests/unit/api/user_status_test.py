from json import loads
from unittest import TestCase
from unittest.mock import patch
from tests.unit.api.test_setup_resources import sample_records
from api.user_status import user_status_handler
from lib.dynamodb import user_table, accounts_table, scans_table


def make_event(email=None, bad_event=False):
    return {
        'requestContext': {
            'authorizer': {
                'claims': {
                    'email': email
                } if not bad_event else {}
            }
        }
    }


class TestUserStatusHandler(TestCase):
    """
    -assumes tables are already made locally, and env variables set accordingly
    """

    @patch.object(user_table, 'get_user')
    def test_nonuser(self, mock_get_user):
        mock_get_user.return_value = None
        response = user_status_handler(make_event('unknown0@gmail.com'), None)
        body = loads(response['body'])
        assert response['statusCode'] == 200
        assert 'email' not in body.keys()

    @patch.object(scans_table, 'get_latest_complete_scan')
    @patch.object(user_table, 'get_user')
    def test_user(self, mock_get_user, mock_get_latest_complete_scan):
        mock_get_latest_complete_scan.return_value = sample_records.LATEST_SCAN['scanId']
        mock_get_user.return_value = sample_records.REGULAR_USER
        response = user_status_handler(make_event('example1@gmail.com'), None)
        body = loads(response['body'])
        assert body['email'] == 'example1@gmail.com'
        assert body['scan']['lastScanDate'] == '2021-05-03T17:32:28Zueoharuoreagkx'
        assert not body['isAdmin']
        assert not body.get('usersList')
        assert not body.get('payerAccounts')
        assert 'spreadsheetUrl' in body

    @patch.object(scans_table, 'get_latest_complete_scan')
    @patch.object(accounts_table, 'scan_all')
    @patch.object(user_table, 'scan_all')
    @patch.object(user_table, 'get_user')
    def test_admin(self, mock_get_user, mock_scan_all_users, mock_scan_all_accounts, mock_get_latest_complete_scan):
        mock_get_latest_complete_scan.return_value = sample_records.LATEST_SCAN['scanId']
        mock_scan_all_accounts.return_value = sample_records.ACCOUNTS_DATA
        mock_get_user.return_value = sample_records.ADMIN_USER
        mock_scan_all_users.return_value = sample_records.USER_DATA
        response = user_status_handler(make_event('admin2@gmail.com'), None)
        body = loads(response['body'])
        assert body['email'] == 'admin2@gmail.com'
        assert body['scan']['lastScanDate'] == '2021-05-03T17:32:28Zueoharuoreagkx'
        assert body['isAdmin']
        assert body.get('usersList')
        assert body.get('payerAccounts')
        assert 'spreadsheetUrl' in body

    def test_no_email(self):
        response = user_status_handler(make_event(bad_event=True), None)
        body = loads(response['body'])
        assert response['statusCode'] == 400
        assert 'email' not in body.keys()
