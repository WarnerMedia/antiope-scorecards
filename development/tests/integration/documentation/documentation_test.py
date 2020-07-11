from tests.integration.util.api import get_api


def test_get_documentation_admin(admin):
    api = get_api(admin['token'])
    result = api.get_documentation()
    assert '<html>' in result
    assert '</html>' in result


def test_get_documentation_user(user):
    api = get_api(user['token'])
    result = api.get_documentation()
    assert '<html>' in result
    assert '</html>' in result


def test_get_documentation_not_authenticated(not_authenticated):
    api = get_api(not_authenticated['token'])
    result = api.get_documentation()
    assert '<html>' in result
    assert '</html>' in result
