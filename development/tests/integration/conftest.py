import pytest

from tests.integration.util import auth, db_seed, db_read


def create_users():
    auth.create_user(auth.credentials['admin'])
    auth.create_user(auth.credentials['user'])
    auth.create_user(auth.credentials['not_authenticated'])


def delete_users():
    auth.delete_user(auth.credentials['admin'])
    auth.delete_user(auth.credentials['user'])
    auth.delete_user(auth.credentials['not_authenticated'])
    db_seed.delete_admin(auth.credentials['admin']['username'])
    db_seed.delete_admin(auth.credentials['user']['username'])


@pytest.fixture(scope='session', autouse=True)
def before_all(request):
    create_users()
    request.addfinalizer(delete_users)


@pytest.fixture(scope='session')
def requirements(before_all):
    requirements = db_read.scan_requirements()
    return requirements


@pytest.fixture(scope='session')
def ncrs(before_all):
    ncr_records = db_read.scan_ncrs()
    return ncr_records


@pytest.fixture(scope='session')
def exclusion_types(before_all):
    exclusion_config = db_read.get_config('exclusions')
    return exclusion_config


@pytest.fixture(scope='session')
def admin(before_all):
    admin_record = db_seed.create_admin(auth.credentials['admin']['username'])
    jwt = auth.get_jwt(auth.credentials['admin'])
    return {**admin_record, 'token': jwt}


@pytest.fixture(scope='session')
def user(before_all):
    user_record = db_seed.create_user(auth.credentials['user']['username'], {
        '123456789012': {
            'permissions': {
                'requestExclusion': False,
                'triggerRemediations': False,
            },
        },
    })
    jwt = auth.get_jwt(auth.credentials['user'])
    return {**user_record, 'token': jwt}


@pytest.fixture(scope='session')
def not_authenticated(before_all):
    jwt = auth.get_jwt(auth.credentials['not_authenticated'])
    return {'token': jwt}
