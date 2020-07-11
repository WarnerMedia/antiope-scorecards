from lib.dynamodb import requirements_table


class TestRequirementsTable():
    def test_check_requirement_applies_to_account(self):
        restricted_requirement = {
            'onlyAppliesTo': ['special']
        }
        unrestricted_requirement = {
        }

        special_account = {
            'scorecard_profile': 'special'
        }

        regular_account = {
        }

        assert requirements_table.check_requirement_applies_to_account(restricted_requirement, special_account)
        assert not requirements_table.check_requirement_applies_to_account(restricted_requirement, regular_account)
        assert requirements_table.check_requirement_applies_to_account(unrestricted_requirement, special_account)
        assert requirements_table.check_requirement_applies_to_account(unrestricted_requirement, regular_account)
