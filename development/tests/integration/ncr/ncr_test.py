import pytest
from tests.integration.util.api import get_api

def test_get_ncr_admin(admin):
    api = get_api(admin['token'])
    result = api.get_ncr(account_id=['123456789012'])
    assert result.ncr_records == []

def test_get_ncr_user(user):
    account_id = list(user['accounts'].keys())[0]
    api = get_api(user['token'])
    result = api.get_ncr(account_id=[account_id])
    assert result.ncr_records == []

def test_get_ncr_not_authenticated(not_authenticated):
    api = get_api(not_authenticated['token'])
    with pytest.raises(Exception) as excinfo:
        api.get_ncr(account_id=['123456789012'])
    assert excinfo.value.status == 403
