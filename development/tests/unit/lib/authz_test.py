"""unit tests for app/lib/authz.py"""
import pytest
from lib import authz
from lib.lambda_decorator.exceptions import HttpForbiddenException


class TestAuthentication:
    def test_is_admin(self):
        test_user = {
            'isAdmin': True,
        }

        result, message = authz.is_admin(test_user)
        assert result is True
        assert message is None

        test_user['isAdmin'] = False
        result, message = authz.is_admin(test_user)
        assert result is False
        assert message is not None

    def test_can_read_account(self):
        test_user = {
            'accounts': {
                '101010': {},
                '505050': {}, }
        }
        test_account_ids = ['101010', '505050']

        result, message = authz.can_read_account(test_user, test_account_ids)
        assert result is True
        assert message is None

        test_account_ids.append('606060')
        result, message = authz.can_read_account(test_user, test_account_ids)
        assert result is False
        assert message == 'user is not authorized for account 606060'

    def test_require_can_read_account(self):
        test_user = {
            'accounts': {
                '101010': {},
                '505050': {}, }
        }
        test_account_ids = ['101010', '505050']

        authz.require_can_read_account(test_user, test_account_ids)

        test_account_ids.append('606060')
        with pytest.raises(HttpForbiddenException):
            authz.require_can_read_account(test_user, test_account_ids)

    def test_can_read_account_true(self):
        user = {
            'accounts': {
                '123456789': {}
            }
        }
        result = authz.can_read_account(user, ['123456789'])
        assert result == (True, None)

    def test_can_read_account_false(self):
        user = {
            'accounts': {
                '123456789': {}
            }
        }
        result = authz.can_read_account(user, '999999999')
        assert result == (False, 'user is not authorized for account 999999999')

    def test_require_can_read_account_true(self):
        user = {
            'accounts': {
                '123456789': {}
            }
        }
        try:
            authz.require_can_read_account(user, '123456789')
        except HttpForbiddenException:
            pytest.fail('HttpForbiddenException raised unexpectedly')

    def test_require_can_read_account_false(self):
        user = {
            'accounts': {
                '123456789': {}
            }
        }
        with pytest.raises(HttpForbiddenException):
            authz.require_can_read_account(user, '999999999')
