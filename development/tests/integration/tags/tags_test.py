from tests.integration.util.api import get_api


def test_get_tags_admin(admin, ncrs):
    api = get_api(admin['token'])
    ncr = ncrs[0]
    ncr_id = '#'.join([ncr['scanId'], ncr['accntId_rsrceId_rqrmntId']])
    result = api.get_tags(
        ncr_id=ncr_id
    )
    assert result.ncr_tags.ncr_id == ncr_id
    assert isinstance(result.ncr_tags.tags, list)
