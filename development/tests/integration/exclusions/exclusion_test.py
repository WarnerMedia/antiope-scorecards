from datetime import datetime, timedelta

from tests.integration.util.api import get_api


def test_put_exclusions_admin(admin, requirements, exclusion_types):
    api = get_api(admin['token'])
    requirement = requirements[0]
    exclusion_type = requirement['exclusionType']
    exclusion_config = exclusion_types[exclusion_type]
    form_fields = {key: 'sampletext' for key, value in exclusion_config['formFields'].items()}
    create_response = api.put_exclusions({
        'exclusion': {
            'accountId': '*',
            'resourceId': 'someresource',
            'requirementId': requirement['requirementId'],
            'status': 'initial',
            'formFields': form_fields,
            'expirationDate': (datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d'),
        },
    })
    assert create_response.new_exclusion.exclusion_id == '#'.join(['*', requirements[0]['requirementId'], 'someresource'])
    # empty deleteExclusion
    for value in create_response.to_dict().get('delete_exclusion', {}).values():
        assert value is None

    update_replacement_response = api.put_exclusions({
        'exclusionId': '#'.join(['*', requirements[0]['requirementId'], 'someresource']),
        'exclusion': {
            'accountId': '*',
            'resourceId': 'otherresource',
            'status': 'initial',
        },
    })
    assert update_replacement_response.new_exclusion.exclusion_id == '#'.join(['*', requirements[0]['requirementId'], 'otherresource'])
    assert update_replacement_response.delete_exclusion.exclusion_id == '#'.join(['*', requirements[0]['requirementId'], 'someresource'])

    result = api.get_exclusions()
    for exclusion in result.exclusions:
        assert exclusion.exclusion_id == '#'.join([exclusion.account_id, exclusion.requirement_id, exclusion.resource_id])
