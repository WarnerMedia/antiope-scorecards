from tests.integration.util.api import get_api
from tests.integration.util.db_seed import create_account, delete_account

def test_get_summary(admin):
    account_id = '012345678922'
    api = get_api(admin['token'])
    create_account(
        {'accountId': account_id}
    )
    result = api.get_account_summary(
        account_ids=account_id
    )
    delete_account(account_id)
    assert len(result.accounts) == 1
    for account in result.accounts:  # object is iterable but not subscriptable.
        assert account.account_id == account_id
        assert account.account_name == account_id
        assert account.critical_count is None
        assert account.current_score is None
        assert account.historical_scores == []


def test_get_summary_two_accounts(admin):
    account_ids = ['012345678944', '012345678955']
    api = get_api(admin['token'])
    create_account(
        {'accountId': account_ids[0]}
    )
    create_account(
        {'accountId': account_ids[1]}
    )
    result = api.get_account_summary(
        account_ids=f'{account_ids[0]},{account_ids[1]}'
    )
    delete_account(account_ids[0])
    delete_account(account_ids[1])
    assert len(result.accounts) == 2
    for account in result.accounts:  # object is iterable but not subscriptable.
        assert account.account_id in account_ids
        assert account.account_name in account_ids
        account_ids.remove(account.account_id)
        assert account.critical_count is None
        assert account.current_score is None
        assert account.historical_scores == []
