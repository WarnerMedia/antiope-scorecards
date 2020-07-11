def lambda_response(payload):
    return payload

def get_success_expected_calls(num_of_accounts=4):
    account_ids = ['000000000000' + str(i + 1) for i in range(num_of_accounts)]
    s3_requirements_ids = ['req1', 'req2', 'req3']
    scan_id = '2020/04/20T12:00:00.123#qwerasdf'
    user_emails = ['a@example.com', 'b@example.com']
    payer_ids = ['p1', 'p2', 'p3']
    cloudsploit_settings_map = {
        'default': {
            'setting_value': False,
            'other_setting': 100
        },
        'extra_secure': {
            'setting_value': True,
            'other_setting': 10
        }
    }

    cloudsploit_scanner_data = {
        'aws': {
            'accountId': '123456789012',
            'externalId': '123',
        },
        'settings': {
            'allow_some_cs_plugin_value': 100
        },
        's3Prefix': '123456789012'
    }
    normal_success_path = {
        'OpenScan': [{
            'expected': {},
            'reply': {'scanId': scan_id}
        }],
        'Load': [{
            'expected': {
                'openScan': {'scanId': scan_id}
            },
            'reply': {
                'accountIds': account_ids,
                's3RequirementIds': s3_requirements_ids,
                'payerIds': payer_ids,
                'cloudsploitSettingsMap': cloudsploit_settings_map
            }
        }],
        'S3Import': [
            [{
                'expected': {
                    'scanId': scan_id,
                    'requirementId': req,
                    'accountIds': account_ids
                }, 'reply': {}
            } for req in s3_requirements_ids]
        ],
        'CloudSploitSetup': [
            [{
                'expected': {
                    'accountId': account_id,
                    'scanId': scan_id,
                    'cloudsploitSettingsMap': cloudsploit_settings_map
                },
                'reply': cloudsploit_scanner_data
            } for account_id in account_ids]
        ],
        'CloudSploitScanningFunctionArn': [
            [{
                'expected': cloudsploit_scanner_data,
                'reply': 'OK'
            } for account_id in account_ids]
        ],
        'CloudSploitPopulate': [
            [{
                'expected': {
                    'accountId': account_id,
                    'scanId': scan_id,
                    'cloudsploitSetup': lambda_response(cloudsploit_scanner_data),
                    'cloudsploitSettingsMap': cloudsploit_settings_map
                },
                'reply': {}
            } for account_id in account_ids]
        ],
        'Exclude': [{
            'expected': {
                'openScan': {'scanId': scan_id},
                'load': {
                    'accountIds': account_ids,
                    's3RequirementIds': s3_requirements_ids,
                    'payerIds': payer_ids,
                    'cloudsploitSettingsMap': cloudsploit_settings_map,
                },
            },
            'reply': {},
        }],
        'ScoreCalculations': [{
            'expected': {
                'openScan': {'scanId': scan_id},
                'load': {
                    'accountIds': account_ids,
                    's3RequirementIds': s3_requirements_ids,
                    'payerIds': payer_ids,
                    'cloudsploitSettingsMap': cloudsploit_settings_map,
                },
            },
            'reply': {},
        }],
        'SetupUserSpreadsheets': [
            {
                'expected': {
                    'openScan': {'scanId': scan_id},
                    'load': {
                        'accountIds': account_ids,
                        's3RequirementIds': s3_requirements_ids,
                        'payerIds': payer_ids,
                        'cloudsploitSettingsMap': cloudsploit_settings_map,
                    },
                },
                'reply': {
                    'openScan': {'scanId': scan_id},
                    'userEmails': user_emails
                }
            }
        ],
        'GenerateSpreadsheets': [
            [{
                'expected': {
                    'openScan': {'scanId': scan_id},
                    'load': {
                        'accountIds': account_ids,
                        's3RequirementIds': s3_requirements_ids,
                        'payerIds': payer_ids,
                        'cloudsploitSettingsMap': cloudsploit_settings_map,
                    },
                },
                'reply': {}}] +
            [{
                'expected': {
                    'accountId': account_id,
                    'openScan': {'scanId': scan_id},
                },
                'reply': {}
            } for account_id in account_ids] +
            [{
                'expected': {
                    'userEmail': user_email,
                    'openScan': {'scanId': scan_id},
                },
                'reply': {}
            } for user_email in user_emails] +
            [{
                'expected': {
                    'payerId': payer_id,
                    'openScan': {'scanId': scan_id},
                },
                'reply': {}
            } for payer_id in payer_ids]
        ],
        'CloseScan': [{
            'expected': {
                'openScan': {
                    'scanId': scan_id,
                },
                'load': {
                    'accountIds': account_ids,
                    's3RequirementIds': s3_requirements_ids,
                    'payerIds': payer_ids,
                    'cloudsploitSettingsMap': cloudsploit_settings_map,
                },
            },
            'reply': {},
        }],
    }
    return normal_success_path
