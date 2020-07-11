from boto3.dynamodb.conditions import Attr
from lib.dynamodb.table_base import TableBase


class RequirementsTable(TableBase):
    def get_cloudsploit_based_requirements(self):
        return self.scan(
            FilterExpression=Attr('source').eq('cloudsploit'))['Items']

    def get(self, requirement_id: str):
        return self.get_item(Key={'requirementId': requirement_id}).get('Item', {})

    def check_requirement_applies_to_account(self, requirement, account):
        """
        Returns if requirement applies to account based on
        requirement's onlyAppliesTo and account scorecard_profile
        """

        # requirements apply to all accounts unless 'onlyAppliesTo' is set
        # if onlyAppliesTo is set, the requirement only applies if
        # account's scorecard_profile is in the onlyAppliesTo list
        if 'onlyAppliesTo' in requirement:
            if 'scorecard_profile' in account:
                applies_to = requirement['onlyAppliesTo']
                # handle string or list of strings
                if isinstance(applies_to, str):
                    applies_to = [applies_to]
                return account['scorecard_profile'] in applies_to
            else:
                return False
        else:
            return True
