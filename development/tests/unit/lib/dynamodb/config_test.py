from lib.dynamodb import config_table

class PassTestConfigTable:
    def test_get_config(self):
        test_config = {
            'configId': config_table.EXCLUSIONS,
            'config': 'configurations',
        }
        config_table.put_item(Item=test_config)

        assert test_config['config'] == config_table.get_config(test_config['configId'])

    def test_set_config(self):
        test_config = {
            'configId': config_table.EXCLUSIONS,
            'config': 'configurations',
        }

        config_table.put_item(Item=test_config)
        config_table.set_config(test_config['configId'], 'configuration2')

        config_from_dynamodb = config_table.get_config(test_config['configId'])

        assert config_from_dynamodb == 'configuration2'
