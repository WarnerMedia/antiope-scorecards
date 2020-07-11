from lib.dynamodb.table_base import TableBase


class ConfigTable(TableBase):
    EXCLUSIONS = 'exclusions'
    VERSION = 'version'
    SEVERITYCOLORS = 'severityColors'
    SEVERITYWEIGHTS = 'severityWeightings'
    REMEDIATIONS = 'remediations'

    def get_config(self, key):
        config_from_dynamodb = self.get_item(Key={'configId': key})
        return config_from_dynamodb.get('Item', {}).get('config', {})

    def set_config(self, key, config):
        config_from_dynamodb = self.get_config(key)
        if config_from_dynamodb != config:
            self.put_item(
                Item={
                    'configId': key,
                    'config': config,
                },
            )
