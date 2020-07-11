from tests.integration.util.api import get_api


def test_get_user_status_admin(admin):
    api = get_api(admin['token'])
    result = api.get_user_status()
    assert result.is_authenticated is True
    assert result.is_admin is True
    assert result.email == admin['email']
    assert result.requirements
    assert result.severity_colors
    assert result.exclusion_types


def test_get_user_status_user(user):
    api = get_api(user['token'])
    result = api.get_user_status()
    assert result.is_authenticated is True
    assert result.is_admin is False
    assert result.email == user['email']
    assert result.requirements
    assert result.severity_colors
    assert result.exclusion_types


def test_get_user_status_not_authenticated(not_authenticated):
    api = get_api(not_authenticated['token'])
    result = api.get_user_status()
    assert result.is_authenticated is False
