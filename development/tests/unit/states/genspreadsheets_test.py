import itertools
import random
from collections import defaultdict
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from lib.dynamodb import accounts_table, scans_table, user_table, config_table
from states import genspreadsheets

NUM_ACCOUNTS = 20
NUM_REQUIREMENTS = 50
ACCOUNT_IDS = [str(random.randrange(100000000000, 999999999999)) for _ in range(NUM_ACCOUNTS)]
SPECIAL_SCORE_MAP = {
    'REQDNC': 'DNC',
    'REQNA': 'N/A',
    'REQErr': 'Err',
}
REQUIREMENT_IDS = ['REQ' + str(random.randrange(100, 999)) for _ in range(NUM_REQUIREMENTS)] + list(SPECIAL_SCORE_MAP.keys())
PAYER_ID = 'thepayer'
SEVERITIES = ['info', 'low', 'medium', 'high', 'critical']
SPONSORS = ['Jeff', 'Werner', 'Satya']
WEIGHTS = [0, 10, 50, 100, 1000, 10000]
SOURCES = ['cloudsploit', 's3import']
COMPONENTS = ['account', 'instance']
SERVICES = ['iam', 'aws', 'ec2']
ACCOUNTS = [
    {
        'accountId': account_id,
        'account_id': account_id,
        'exec_sponsor_email': SPONSORS[idx % len(SPONSORS)],
        'account_name': 'aname' + account_id,
        'payer_id': 'PAYER_ID'
    } for idx, account_id in enumerate(ACCOUNT_IDS)
]

REQUIREMENTS = {
    requirement_id: {
        'severity': SEVERITIES[idx % len(SEVERITIES)],
        'description': 'Requirement description for ' + requirement_id,
        'weight': Decimal(WEIGHTS[idx % len(WEIGHTS)]),
        'source': SOURCES[idx % len(SOURCES)],
        'component': COMPONENTS[idx % len(COMPONENTS)],
        'service': SERVICES[idx % len(SERVICES)],
        'requirementId': requirement_id,
        'reason': 'Some reason this shield is included.'

    } for idx, requirement_id in enumerate(REQUIREMENT_IDS)
}
SCAN_ID = 'spreadsheet_test1'
SCORES = defaultdict(lambda: defaultdict(dict))
for account_id in ACCOUNT_IDS:
    for requirement_id, requirement in REQUIREMENTS.items():
        if requirement_id in SPECIAL_SCORE_MAP:
            num_failing = SPECIAL_SCORE_MAP[requirement_id]
            num_resources = SPECIAL_SCORE_MAP[requirement_id]
        else:
            num_failing = Decimal(random.randrange(0, 7))
            num_resources = Decimal(random.randrange(num_failing, num_failing + 5))
            if num_failing == 6:
                num_failing = 'N/A'
        SCORES[account_id][requirement_id] = {
            'accntId_rqrmntId': f'{account_id}#{requirement_id}',
            'accountId': account_id,
            'requirementId': requirement_id,
            'scanId': SCAN_ID,
            'score': {
                requirement['severity']:
                {
                    'numFailing': num_failing,
                    'numResources': num_resources,
                    'weight': requirement['weight'],
                }
            }
        }

NCRS = []
IS_HIDDEN_VALUES = [True, False]
EXCLUSION_APPLIED_VALUES = [True, False, None]
EXPIRATION_DATE_VALUES = ['2999/12/31', '2000/01/01']
for is_hidden, exclusion_applied, expiration_date, requirement_id in itertools.product(
        IS_HIDDEN_VALUES, EXCLUSION_APPLIED_VALUES, EXPIRATION_DATE_VALUES, REQUIREMENTS.keys()):
    resource_id = 'arn:aws:lambda:us-west-2:678678676867:function:test-2-function'
    account_id = ACCOUNT_IDS[0]
    ncr = {
        'accountId': account_id,
        'resourceId': resource_id,
        'accountName': 'aname' + account_id,
        'scanId': SCAN_ID,
        'accntId_rsrceId_rqrmntId': f'{account_id}#{resource_id}#{requirement_id}',
        'requirementId': requirement_id,
        'rqrmntId_accntId': f'{requirement_id}#{account_id}',
        'isHidden': is_hidden
    }

    if exclusion_applied is not None:
        ncr['exclusionApplied'] = exclusion_applied
        ncr['exclusion'] = {
            'accountId': account_id,
            'adminComments': 'looks fine',
            'formFields': {
                'reason': 'not connected to anything'
            },
            'resourceId': resource_id,
            'requirementId': requirement_id,
            'type': 'justification',
            'status': 'approved',
            'expirationDate': expiration_date
        }

    NCRS.append(ncr)


class TestGenSpreadsheets():
    def test_base_workbook(self):
        self.populate_severity()
        workbook = genspreadsheets.create_base_workbook(
            NCRS, ACCOUNTS, REQUIREMENTS, SCORES
        )
        genspreadsheets.add_accounts_tab(workbook, ACCOUNTS, SCORES)
        genspreadsheets.add_sponsor_tab(workbook, ACCOUNTS, SCORES)

        # no assertions, smoke test
        workbook.save('test.local.xlsx')

    def test_get_single_account_by_id(self):
        self.populate_accounts()

        event = {'accountId':'123123123132'}
        accounts, bucket_prefix, scan_type = genspreadsheets.get_accounts(event)

        assert accounts == [{
            'accountId': '123123123132',
            'account_id': '123123123132',
            'payer_id': '11223344556677'
        }]
        assert bucket_prefix == '{}/by-account/123123123132.xlsx'.format(genspreadsheets.PREFIX)
        assert scan_type == genspreadsheets.SheetTypes.SINGLE_ACCOUNT

    def test_get_accounts_by_payer_id(self):
        self.populate_accounts()

        event = {'payerId':'11223344556677'}
        accounts, bucket_prefix, scan_type = genspreadsheets.get_accounts(event)

        assert accounts == [
            {
                'accountId': '345345345345',
                'account_id': '345345345345',
                'payer_id': '11223344556677'
            },
            {
                'accountId': '123123123132',
                'account_id': '123123123132',
                'payer_id': '11223344556677'
            }
        ]
        assert bucket_prefix == '{}/by-payer/11223344556677.xlsx'.format(genspreadsheets.PREFIX)
        assert scan_type == genspreadsheets.SheetTypes.PAYER_ACCOUNT

    def test_get_accounts_by_user_email(self):
        self.populate_accounts()
        self.populate_users()
        event = {'userEmail':'spread_sheet@tester.com'}

        accounts, bucket_prefix, scan_type = genspreadsheets.get_accounts(event)

        assert accounts == [
            {
                'accountId': '567567567567',
                'account_id': '567567567567',
                'payer_id': '00112233445566'
            },
            {
                'accountId': '678678676867',
                'account_id': '678678676867',
                'payer_id': '99887766554433'
            }
        ]
        assert bucket_prefix == '{}/by-user/spread_sheet@tester.com.xlsx'.format(genspreadsheets.PREFIX)
        assert scan_type == genspreadsheets.SheetTypes.USER

    def test_get_all_accounts(self):
        self.populate_accounts()
        event = {}
        accounts, bucket_prefix, scan_type = genspreadsheets.get_accounts(event)

        assert len(accounts) >= 5
        assert bucket_prefix == '{}/global/scorecard-latest.xlsx'.format(genspreadsheets.PREFIX)
        assert scan_type == genspreadsheets.SheetTypes.GLOBAL

    def populate_accounts(self):
        genspreadsheets.CACHE.clear()
        accounts = [
            {
                'accountId': '123123123132',
                'account_id': '123123123132',
                'payer_id': '11223344556677'
            },
            {
                'accountId': '345345345345',
                'account_id': '345345345345',
                'payer_id': '11223344556677'
            },
            {
                'accountId': '456456456465',
                'account_id': '456456456465',
                'payer_id': '00112233445566'
            },
            {
                'accountId': '567567567567',
                'account_id': '567567567567',
                'payer_id': '00112233445566'
            },
            {
                'accountId': '678678676867',
                'account_id': '678678676867',
                'payer_id': '99887766554433'
            }
        ]
        accounts_table.batch_put_records(accounts)

    def populate_users(self):
        users = [
            {
                'email': 'spread_sheet@tester.com',
                'firstName': 'generate',
                'lastName': 'spreadsheets',
                'accounts': {
                    '678678676867': {},
                    '567567567567': {}
                }
            }
        ]
        user_table.batch_put_records(users)

    def populate_severity(self):
        config_table.set_config(config_table.SEVERITYCOLORS, {
            'critical': {'background': '000001', 'text': 'FFFFFF'},
            'high':     {'background': 'FF0000', 'text': 'FFFFFF'},
            'medium':   {'background': 'FF8000', 'text': 'FFFFFF'},
            'low':      {'background': 'FFFF00', 'text': '000000'},
            'info':     {'background': '00F000', 'text': '000000'},
            'ok':       {'background': '00FF00', 'text': '000000'},
            })
        config_table.set_config(config_table.SEVERITYWEIGHTS, {
            'critical': 10000,
            'high':     1000,
            'medium':   100,
            'low':      10,
            'info':     0,
            })
        config_table.set_config(config_table.VERSION, 'a version goes here')
        config_table.set_config(config_table.EXCLUSIONS, {
            'exclusionTypes': {
                'exception': {
                    'displayname': 'Exception',
                    'states': {
                        'initial': {
                            'effective': False,
                            'displayName': 'Submitted',
                            'actionName': 'Submit exception'
                        },
                        'approved': {
                            'displayName': 'Approved',
                            'actionName': 'Approve'
                        },
                        'rejected': {
                            'displayName': 'Rejected',
                            'actionName': 'Reject'
                        },
                        'archived': {
                            'displayName': 'Archived',
                            'actionName': 'Archive'
                        }
                    },
                    'formFields': {
                        'reason': {
                            'label': 'Reason',
                            'placeholder': 'Enter reason for not complying with this requirement',
                            'showInNcrView': True
                        }
                    },
                    'defaultDurationInDays': 365,
                    'maxDurationInDays': 1095
                    }
                }
            })

    def test_gen_spreadsheets_error_handler(self):
        scan_id = scans_table.create_new_scan_id()
        scans_table.put_item(
            Item={
                'scan': scans_table.SCAN,
                'processState': scans_table.IN_PROGRESS,
                'scanId': scan_id,
            }
        )

        context = SimpleNamespace()
        context.function_name = 'function-name'

        genspreadsheets.gen_spreadsheets_error_handler(
            {
                'scanId': scan_id,
                'error': 'error'
            },
            context
        )

        expected_result = {
            'scan': scans_table.SCAN,
            'processState': scans_table.IN_PROGRESS,
            'scanId': scan_id,
            'errors': [
                {
                    'functionName': context.function_name,
                    'error': 'error'
                }
            ]
        }

        result = scans_table.get_item(Key={'scan': scans_table.SCAN, 'scanId': scan_id})['Item']
        assert result.pop('ttl')
        assert result == expected_result

class TestSetupUserSpreadsheets():
    @patch('lib.dynamodb.user_table.scan_all')
    def test_setup_user_spreadsheets(self, user_table_scan_all: Mock):
        user_table_scan_all.return_value = [
            {'email': 'example1@example.com'},
            {'email': 'example2@example.com'},
            {'email': 'example3@example.com'},
        ]
        event = {
            'scanId': 'a scan id here',
            'load': {'accountIds': ['1', '2', '3', '4']}
        }
        result = genspreadsheets.setup_user_spreadsheets_handler(event, {})
        assert result == {
            'scanId': 'a scan id here',
            'userEmails': [
                'example1@example.com',
                'example2@example.com',
                'example3@example.com',
            ]
        }
