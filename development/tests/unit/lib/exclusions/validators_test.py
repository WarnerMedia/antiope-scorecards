from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from lib.dynamodb import requirements_table, ncr_table, scans_table
from lib.exclusions import validators
from tests.unit.api.test_setup_resources import sample_records

EXCEPTION = sample_records.EXCLUSION_TYPES['exception']

class TestAccountId:
    def test_account_id(self):
        result, message = validators.account_id({}, {'accountId': '123123123123'}, EXCEPTION, False)
        assert result is True
        assert message is None

    def test_account_id_numeric(self):
        result, message = validators.account_id({}, {'accountId': 'abcabcabcabc'}, EXCEPTION, False)
        assert result is False
        assert message

    def test_account_id_length(self):
        result, message = validators.account_id({}, {'accountId': '123123'}, EXCEPTION, False)
        assert result is False
        assert message

    def test_account_id_wildcard_admin(self):
        result, message = validators.account_id({}, {'accountId': '*'}, EXCEPTION, True)
        assert result is True
        assert message is None

    def test_account_id_wildcard_user(self):
        result, message = validators.account_id({}, {'accountId': '*'}, EXCEPTION, False)
        assert result is False
        assert message


class TestExpirationDate:
    def test_invalid_expiration_date(self):
        result, message = validators.expiration_date({'type': 'exception'}, {'expirationDate': 'invalid-datetime'}, EXCEPTION, True)
        assert result is False
        assert message

    def test_large_expiration_date(self):
        result, message = validators.expiration_date({'type': 'exception'}, {
            'expirationDate': (datetime.now() + timedelta(days=sample_records.EXCLUSION_TYPES['exception']['maxDurationInDays'] + 1)).strftime('%Y/%m/%d'),
        }, EXCEPTION, False)
        assert result is False
        assert message

    def test_valid_expiration_date(self):
        result, message = validators.expiration_date({'type': 'exception'}, {
            'expirationDate': (datetime.now() + timedelta(days=sample_records.EXCLUSION_TYPES['exception']['maxDurationInDays'] - 1)).strftime('%Y/%m/%d'),
        }, EXCEPTION, False)
        assert result is True
        assert message is None

    def test_negative_expiration_date(self):
        result, message = validators.expiration_date({'type': 'exception'}, {
            'expirationDate': (datetime.now() + timedelta(days=-1)).strftime('%Y/%m/%d'),
        }, EXCEPTION, False)
        assert result is False
        assert message


class TestResourceId:
    @patch.object(ncr_table, 'get_item', Mock(return_value={'Item': {'ncr':'resource'}}))
    @patch.object(scans_table, 'get_latest_complete_scan', Mock(return_value='latest-scan'))
    def test_resource_id(self):
        result, message = validators.resource_id({'type': 'exception'}, {
            'accountId': '123123123123',
            'requirementId': 'My-Requirement',
            'resourceId': 'resource',
        }, EXCEPTION, False)
        assert result is True
        assert message is None

    @patch.object(ncr_table, 'get_item', Mock(return_value={'Item': {}}))
    @patch.object(scans_table, 'get_latest_complete_scan', Mock(return_value='latest-scan'))
    def test_no_resource(self):
        result, message = validators.resource_id({'type': 'exception'}, {
            'accountId': '123123123123',
            'requirementId': 'My-Requirement',
            'resourceId': 'resource',
        }, EXCEPTION, False)
        assert result is False
        assert message

    @patch.object(ncr_table, 'get_item', Mock(return_value={'Item': {'ncr':'resource'}}))
    @patch.object(scans_table, 'get_latest_complete_scan', Mock(return_value='latest-scan'))
    def test_wildcard_user(self):
        result, message = validators.resource_id({'type': 'exception'}, {
            'accountId': '123123123123',
            'requirementId': 'My-Requirement',
            'resourceId': '*',
        }, EXCEPTION, False)
        assert result is False
        assert message

    @patch.object(ncr_table, 'get_item', Mock(return_value={'Item': {'ncr':'resource'}}))
    @patch.object(scans_table, 'get_latest_complete_scan', Mock(return_value='latest-scan'))
    def test_wildcard_admin(self):
        result, message = validators.resource_id({'type': 'exception'}, {
            'accountId': '123123123123',
            'requirementId': 'My-Requirement',
            'resourceId': '*',
        }, EXCEPTION, True)
        assert result is True
        assert message is None


class TestRequirementId:
    @patch.object(requirements_table, 'get_item', Mock(return_value={'Item': {'ncr':'resource'}}))
    def test_resource_id(self):
        result, message = validators.requirement_id({'type': 'exception'}, {
            'accountId': '123123123123',
            'requirementId': 'My-Requirement',
            'resourceId': 'resource',
        }, EXCEPTION, False)
        assert result is True
        assert message is None

    @patch.object(requirements_table, 'get_item', Mock(return_value={'Item': {}}))
    def test_missing_resource(self):
        result, message = validators.requirement_id({'type': 'exception'}, {
            'accountId': '123123123123',
            'requirementId': 'My-Requirement',
            'resourceId': 'resource',
        }, EXCEPTION, False)
        assert result is False
        assert message

    @patch.object(requirements_table, 'get_item', Mock(return_value={'Item': {'ncr':'resource'}}))
    def test_wildcard_user(self):
        result, message = validators.requirement_id({'type': 'exception'}, {
            'accountId': '123123123123',
            'requirementId': '*',
            'resourceId': 'resource',
        }, EXCEPTION, False)
        assert result is False
        assert message

    @patch.object(requirements_table, 'get_item', Mock(return_value={'Item': {'ncr':'resource'}}))
    def test_wildcard_admin(self):
        result, message = validators.requirement_id({'type': 'exception'}, {
            'accountId': '123123123123',
            'requirementId': '*',
            'resourceId': 'resource',
        }, EXCEPTION, False)
        assert result is False
        assert message


class TestFormFields:
    def test_form_fields(self):
        result, message = validators.form_fields({'type': 'exception'}, {
            'formFields': {
                'reason': 'because',
            },
        }, EXCEPTION, False)
        assert result is True
        assert message is None

    def test_form_fields_invalid(self):
        result, message = validators.form_fields({'type': 'exception'}, {
            'formFields': {
                'invalid-form-field': 'because',
            },
        }, EXCEPTION, False)
        assert result is False
        assert message


class TestUpdateRequested:
    def test_update_requested_form_fields(self):
        result, message = validators.update_requested({'type': 'exception'}, {
            'updateRequested': {
                'formFields': {
                    'reason': 'because',
                },
            },
        }, EXCEPTION, False)
        assert result is True
        assert message is None


    def test_update_requested_form_fields_invalid(self):
        result, message = validators.update_requested({'type': 'exception'}, {
            'updateRequested': {
                'formFields': {
                    'invalid-field': 'because',
                },
            },
        }, EXCEPTION, False)
        assert result is False
        assert message


    def test_update_requested_datetime(self):
        max_days = sample_records.EXCLUSION_TYPES['exception']['maxDurationInDays']
        result, message = validators.update_requested({
            'type': 'exception',
            'accountId': '123123123123',
            'expirationDate': (datetime.now() + timedelta(days=max_days - 1)).strftime('%Y/%m/%d'),
        }, {
            'updateRequested': {
                'expirationDate': (datetime.now() + timedelta(days=max_days - 3)).strftime('%Y/%m/%d'),
            },
        }, EXCEPTION, False)
        assert result is True
        assert message is None


    def test_update_requested_datetime_invalid(self):
        max_days = sample_records.EXCLUSION_TYPES['exception']['maxDurationInDays']
        result, message = validators.update_requested({
            'type': 'exception',
            'accountId': '123123123123',
            'expirationDate': (datetime.now() + timedelta(days=max_days - 1)).strftime('%Y/%m/%d'),
        }, {
            'updateRequested': {
                'expirationDate': (datetime.now() + timedelta(days=max_days + 1)).strftime('%Y/%m/%d'),
            },
        }, EXCEPTION, False)
        assert result is False
        assert message


    def test_update_requested_datetime_not_parsable(self):
        max_days = sample_records.EXCLUSION_TYPES['exception']['maxDurationInDays']
        result, message = validators.update_requested({
            'type': 'exception',
            'accountId': '123123123123',
            'expirationDate': (datetime.now() + timedelta(days=max_days - 3)).strftime('%Y/%m/%d'),
        }, {
            'updateRequested': {
                'expirationDate': 'bad-datetime',
            },
        }, EXCEPTION, False)
        assert result is False
        assert message


    def test_update_requested_extra_keys(self):
        max_days = sample_records.EXCLUSION_TYPES['exception']['maxDurationInDays']
        result, message = validators.update_requested({
            'type': 'exception',
            'accountId': '123123123123',
            'expirationDate': (datetime.now() + timedelta(days=max_days - 3)).strftime('%Y/%m/%d'),
        }, {
            'updateRequested': {
                'extraKey': 'extraValue'
            },
        }, EXCEPTION, False)
        assert result is False
        assert message


class TestAdminComments:
    def test_admin_comments(self):
        result, message = validators.admin_comments({'type': 'exception'}, {
            'adminComments': 'administrative messaging',
        }, EXCEPTION, False)
        assert result is True
        assert message is None

    def test_admin_comments_not_string(self):
        result, message = validators.admin_comments({'type': 'exception'}, {
            'adminComments': {'something': 'weird'},
        }, EXCEPTION, False)
        assert result is False
        assert message


class TestHidesResources:
    def test_hides_resources(self):
        result, message = validators.hides_resources({'type': 'exception'}, {
            'hidesResources': True,
        }, EXCEPTION, False)
        assert result is True
        assert message is None

    def test_hides_resources_not_string(self):
        result, message = validators.hides_resources({'type': 'exception'}, {
            'hidesResources': {'something': 'weird'},
        }, EXCEPTION, False)
        assert result is False
        assert message
