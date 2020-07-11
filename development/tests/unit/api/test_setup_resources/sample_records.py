from boto3.dynamodb.types import Decimal
from lib.dynamodb.scans import (
    ScansTable
)
from lib.dynamodb import (
    scans_table, user_table, requirements_table,
    ncr_table, accounts_table,
    scores_table, account_scores_table
)


ACCOUNTS_DATA = [{
    'accountId': '111111111111',
    'account_name': 'Sample text',
    'account_status': 'ACTIVE',
    'assume_role_link': 'No Cross Account Role',
    'exec_sponsor': 'sampletext@gmail.com',
    'exec_sponsor_email': 'sampletext@gmail.com',
    'payer_id': '888',
    'payer_name': 'sampletextmaster',
}, {
    'accountId': '999999999999',
    'account_name': 'Sample text',
    'account_status': 'ACTIVE',
    'assume_role_link': 'No Cross Account Role',
    'exec_sponsor': 'sampletext@gmail.com',
    'exec_sponsor_email': 'sampletext@gmail.com',
    'payer_id': '888',
    'payer_name': 'sampletextmaster',
}, {
    'accountId': '888',
    'account_name': 'Sample text',
    'account_status': 'ACTIVE',
    'assume_role_link': 'No Cross Account Role',
    'exec_sponsor': 'sampletext@gmail.com',
    'exec_sponsor_email': 'sampletext@gmail.com',
    'payer_id': '888',
    'payer_name': 'sampletextmaster',
}]

ADMIN_USER = {
    'isAdmin': True,
    'email': 'admin2@gmail.com',
    'firstName': 'AdrianAdmin',
    'lastName': 'Towner',
    'accounts': {
        '111111111111': {
            'permissions': {
                'requestExclusion': True,
                'triggerRemediation': True,
            }
        }
    }
}

REGULAR_USER = {
    'isAdmin': False,
    'email': 'example1@gmail.com',
    'firstName': 'Jill',
    'lastName': 'Smith',
    'accounts': {
        '123123123123': {
            'permissions': {
                'requestExclusion': True,
                'requestExclusionExtension': True,
                'triggerRemediation': True,
            }
        },
        '111111111111': {
            'permissions': {
                'requestExclusion': True,
                'requestExclusionExtension': True,
                'triggerRemediation': True,
            }
        },
        '222222222222': {
            'permissions': {
                'requestExclusion': True,
                'requestExclusionExtension': True,
                'triggerRemediation': True,
            }
        }
    }
}

USER_DATA = [REGULAR_USER.copy(), ADMIN_USER.copy()]

LATEST_SCAN = {
    'scan': ScansTable.SCAN,
    'scanId': '2021-05-03T17:32:28Zueoharuoreagkx',
    'status': ScansTable.COMPLETED,
    'iteratorErrors': 'None',
    'errors': 'None',
}

SCAN_DATA = [
    {
        'scan': ScansTable.SCAN,
        'scanId': '2020-04-01T17:32:28Zreoauaoeurgo',
        'staus': ScansTable.IN_PROGRESS,
        'iteratorErrors': 'None',
        'errors': 'None',
    },
    {
        'scan': ScansTable.SCAN,
        'scanId': '2020-04-05T17:32:28Zueorakxroerk',
        'status': ScansTable.COMPLETED,
        'iteratorErrors': 'None',
        'errors': 'None',
    },
    LATEST_SCAN,
    {
        'scan': ScansTable.SCAN,
        'scanId': '2019-04-05T17:32:28Zueorakxroerk',
        'status': ScansTable.ERRORED,
        'iteratorErrors': 'None',
        'errors': 'None',
    },
]

REQUIREMENTS_DATA = [
    {
        'requirementId': 'bbb',
        'description': 'sample text',
        'source': 'cloudsploit',
    },
    {
        'requirementId': 'ccc',
        'description': 'sample text',
        'source': 's3Import',
    },
    {
        'requirementId': 'ddd',
        'description': 'sample text',
        'source': 'cloudsploit',
        'severity': 'critical',
    },
    {
        'requirementId': 'eee',
        'description': 'sample text',
        'source': 's3Import',
        'severity': 'critical',
    },
    {
        'requirementId': 'fff',
        'description': 'sample text',
        'source': 's3Import',
        'severity': 'high',
    },
]

SCORES_DATA = [
    {
        'scanId': '2020-05-03T17:32:28Zueoharuoreagkx',
        'accntId_rqrmntId': '111111111111_req1',
        'accountId': '111111111111',
        'requirementId': 'req1',
        'score': {
            'weight': '.5',
            'score': '.9'
        }
    },
    {
        'accntId_rqrmntId': '111111111111_req2',
        'scanId': '2021-05-03T17:32:28Zueoharuoreagkx',
        'accountId': '111111111111',
        'requirementId': 'req2',
        'score': {
            'weight': '.3',
            'score': '.9'
        }
    },
    {
        'accntId_rqrmntId': '111111111111_req5',
        'scanId': '2021-05-03T17:32:28Zueoharuoreagkx',
        'accountId': '111111111111',
        'requirementId': 'req5',
        'score': {
            'weight': '.3',
            'score': '.3'
        }
    },
    {
        'accntId_rqrmntId': '111111111111_req3',
        'scanId': '2021-05-03T17:32:28Zueoharuoreagkx',
        'accountId': '111111111111',
        'requirementId': 'req3',
        'score': {
            'weight': '.3',
            'score': scores_table.DATA_NOT_COLLECTED
        }
    },
    {
        'accntId_rqrmntId': '111111111111_req4',
        'scanId': '2021-05-03T17:32:28Zueoharuoreagkx',
        'accountId': '111111111111',
        'requirementId': 'req4',
        'score': {
            'weight': '.3',
            'score': scores_table.DATA_NOT_COLLECTED
        }
    },
    {
        'accntId_rqrmntId': '222222222222_req1',
        'scanId': '2020-05-03T17:32:28Zueoharuoreagkx',
        'accountId': '222222222222',
        'requirementId': 'req1',
        'score': {
            'weight': '.1',
            'score': '1'
        }
    },
    {
        'accntId_rqrmntId': '222222222222_req2',
        'scanId': '2021-05-03T17:32:28Zueoharuoreagkx',
        'accountId': '222222222222',
        'requirementId': 'req2',
        'score': {
            'weight': '.5',
            'score': '0'
        }
    },
    {
        'accntId_rqrmntId': '222222222222_req3',
        'scanId': '2021-05-03T17:32:28Zueoharuoreagkx',
        'accountId': '222222222222',
        'requirementId': 'req3',
        'score': {
            'weight': '.3',
            'score': scores_table.DATA_NOT_COLLECTED
        }
    },
    {
        'accntId_rqrmntId': '222222222222_req4',
        'scanId': '2021-05-03T17:32:28Zueoharuoreagkx',
        'accountId': '222222222222',
        'requirementId': 'req4',
        'score': {
            'weight': '.3',
            'score': scores_table.DATA_NOT_COLLECTED
        }
    },
    {
        'accntId_rqrmntId': '222222222222_req5',
        'scanId': '2021-05-03T17:32:28Zueoharuoreagkx',
        'accountId': '222222222222',
        'requirementId': 'req5',
        'score': {
            'weight': '.8',
            'score': '.1'
        }
    },
    {
        'accntId_rqrmntId': '111111111111_req1',
        'scanId': '2020-04-05T17:32:28Zueorakxroerk',
        'accountId': '111111111111',
        'requirementId': 'req1',
        'score': {
            'weight': '.3',
            'score': '.5'
        }
    },
    {
        'accntId_rqrmntId': '222222222222_req1',
        'scanId': '2020-04-05T17:32:28Zueorakxroerk',
        'accountId': '222222222222',
        'requirementId': 'req1',
        'score': {
            'weight': '.7',
            'score': '.4'
        }
    },
    {
        'accntId_rqrmntId': '111111111111_req1',
        'scanId': '2020-04-02T17:32:28Zueorakxroerk',
        'accountId': '111111111111',
        'requirementId': 'req1',
        'score': {
            'weight': '.2',
            'score': '.3'
        }
    },
    {
        'accntId_rqrmntId': '222222222222_req1',
        'scanId': '2020-04-02T17:32:28Zueorakxroerk',
        'accountId': '222222222222',
        'requirementId': 'req1',
        'score': {
            'weight': '.1',
            'score': '.1'
        }
    },
    {
        'accntId_rqrmntId': '111111111111_req1',
        'scanId': '2020-04-01T17:32:28Zueorakxroerk',
        'accountId': '111111111111',
        'requirementId': 'req1',
        'score': {
            'weight': '.2',
            'score': '.3'
        }
    },
    {
        'accntId_rqrmntId': '222222222222_req1',
        'scanId': '2020-04-01T17:32:28Zueorakxroerk',
        'accountId': '222222222222',
        'requirementId': 'req1',
        'score': {
            'weight': '.1',
            'score': '.1'
        }
    }
]

NCR_DATA = [
    {
        'scanId': '2021-05-03T17:32:28Zueoharuoreagkx',
        'accntId_rsrceId_rqrmntId': '111111111111_a_ddd',
        'rqrmntId_accntId': 'ddd_111111111111',

        'ncrId': '1',
        'resource': {
            'accountId': '111111111111',
            'accountName': 'sampletext',
            'requirementId': 'ddd',
            'resourceId': 'a',
            'resourceType': 'sampletext',
            'region': 'sampletext',
            'reason': 'sampletext',
            'exclusionReason': 'sampletext',
            'exclusionState': 'sampletext',
            'exclusionApplied': 'sampletext',
            'exclusionType': 'sampletext',
            'exclusionExpiration': 'sampletext',

            'exclusionPendingReason': 'sampletext',
            'exclusionPendingExpiration': 'sampletext',
        },
        'allowedActions': {
            'updateExclusionReason': True,
            'requestExclusion': True,
            'addJustification': True,
            'requestExclusionExtension': True,
            'remediate': True
        }

    },
    {
        'scanId': '2021-05-03T17:32:28Zueoharuoreagkx',
        'accntId_rsrceId_rqrmntId': '111111111111_b_eee',
        'rqrmntId_accntId': 'eee_111111111111',
        'ncrId': '2',
        'resource': {
            'accountId': '111111111111',
            'accountName': 'sampletext',
            'requirementId': 'eee',
            'resourceId': 'b',
            'resourceType': 'sampletext',
            'region': 'sampletext',
            'reason': 'sampletext',
            'exclusionReason': 'sampletext',
            'exclusionState': 'sampletext',
            'exclusionApplied': 'sampletext',
            'exclusionType': 'sampletext',
            'exclusionExpiration': 'sampletext',

            'exclusionPendingReason': 'sampletext',
            'exclusionPendingExpiration': 'sampletext',
        },
        'allowedActions': {
            'updateExclusionReason': True,
            'requestExclusion': True,
            'addJustification': True,
            'requestExclusionExtension': True,
            'remediate': True,
        }

    },
    {
        'scanId': '2021-05-03T17:32:28Zueoharuoreagkx',
        'accntId_rsrceId_rqrmntId': '222222222222_c_ddd',
        'rqrmntId_accntId': 'ddd_222222222222',
        'ncrId': '3',
        'resource': {
            'accountId': '222222222222',
            'accountName': 'sampletext',
            'requirementId': 'ddd',
            'resourceId': 'c',
            'resourceType': 'sampletext',
            'region': 'sampletext',
            'reason': 'sampletext',
            'exclusionReason': 'sampletext',
            'exclusionState': 'sampletext',
            'exclusionApplied': 'sampletext',
            'exclusionType': 'sampletext',
            'exclusionExpiration': 'sampletext',

            'exclusionPendingReason': 'sampletext',
            'exclusionPendingExpiration': 'sampletext',
        },
        'allowedActions': {
            'updateExclusionReason': True,
            'requestExclusion': True,
            'addJustification': True,
            'requestExclusionExtension': True,
            'remediate': True,
        }

    }
]

ACCOUNT_SCORES_DATA = [
    {
        'accountId': '111111111111',
        'date': '2020-03-03',
        'score': {
            'weightedScore': Decimal(str(0.8)),
            'criticalCount': 2
        }
    },
    {
        'accountId': '222222222222',
        'date': '2020-03-03',
        'score': {
            'weightedScore': Decimal(str(.6)),
            'criticalCount': 1
        }
    },
    {
        'accountId': '111111111111',
        'date': '2020-03-01',
        'score': {
            'weightedScore': Decimal(str(.3)),
        }
    },
    {
        'accountId': '222222222222',
        'date': '2020-03-01',
        'score': {
            'weightedScore': Decimal(str(.1)),
        }
    }
]

EXCLUSION_INITIAL = {
    'status': 'initial',
    'accountId': ACCOUNTS_DATA[0]['accountId'],
    'requirementId': REQUIREMENTS_DATA[0]['requirementId'],
    'resourceId': NCR_DATA[0]['resource']['resourceId'],
    'adminComments': 'no it isnt',
    'expirationDate': '2021/05/31',
    'type': 'exception',
    'hidesResources': False,
    'lastStatusChangeDate': '2021/05/01',
    'formFields': {
        'reason': 'its fine'
    },
    'updateRequested': {},
}
EXCLUSION_APPROVED = {
    'status': 'approved',
    'accountId': ACCOUNTS_DATA[0]['accountId'],
    'requirementId': REQUIREMENTS_DATA[0]['requirementId'],
    'resourceId': NCR_DATA[0]['resource']['resourceId'],
    'adminComments': 'no it isnt',
    'expirationDate': '2021/05/31',
    'type': 'exception',
    'hidesResources': False,
    'lastStatusChangeDate': '2021/05/01',
    'formFields': {
        'reason': 'its fine'
    },
    'updateRequested': {},
}
EXCLUSION_REJECTED = {
    'status': 'rejected',
    'accountId': ACCOUNTS_DATA[0]['accountId'],
    'requirementId': REQUIREMENTS_DATA[0]['requirementId'],
    'resourceId': NCR_DATA[0]['resource']['resourceId'],
    'adminComments': 'no it isnt',
    'expirationDate': '2021/05/31',
    'type': 'exception',
    'hidesResources': False,
    'lastStatusChangeDate': '2021/05/01',
    'formFields': {
        'reason': 'its fine'
    },
    'updateRequested': {},
}
EXCLUSION_APPROVED_PENDING_CHANGES = {
    'status': 'approved',
    'accountId': ACCOUNTS_DATA[0]['accountId'],
    'requirementId': REQUIREMENTS_DATA[0]['requirementId'],
    'resourceId': NCR_DATA[0]['resource']['resourceId'],
    'adminComments': 'no it isnt',
    'expirationDate': '2021/05/31',
    'type': 'exception',
    'hidesResources': False,
    'lastStatusChangeDate': '2021/05/01',
    'formFields': {
        'reason': 'its fine'
    },
    'updateRequested': {
        'expirationDate': '2021/05/30'
    },
}
EXCLUSION_ARCHIVED = {
    'status': 'archived',
    'accountId': ACCOUNTS_DATA[0]['accountId'],
    'requirementId': REQUIREMENTS_DATA[0]['requirementId'],
    'resourceId': NCR_DATA[0]['resource']['resourceId'],
    'adminComments': 'no it isnt',
    'expirationDate': '2021/05/31',
    'type': 'exception',
    'hidesResources': False,
    'lastStatusChangeDate': '2021/05/01',
    'formFields': {
        'reason': 'its fine'
    },
    'updateRequested': {},
}


EXCLUSION_TYPES = {
    'exception': {
        'defaultDurationInDays': 365,
        'formFields': {
            'reason': {
                'showInNcrView': True,
                'label': 'Reason',
                'placeholder': 'Enter reason for not complying with this requirement'
            }
        },
        'maxDurationInDays': 1095,
        'displayname': 'Exception',
        'states': {
            'archived': {
                'effective': False,
                'displayName': 'Archived',
                'actionName': 'Archive'
            },
            'approved': {
                'effective': True,
                'displayName': 'Approved',
                'actionName': 'Approve'
            },
            'initial': {
                'effective': False,
                'displayName': 'Submitted',
                'actionName': 'Submit exception'
            },
            'rejected': {
                'effective': False,
                'displayName': 'Rejected',
                'actionName': 'Reject'
            }
        }
    }
}

def run_all():
    for func in (put_mock_userdata, put_mock_accountsdata, put_mock_scoresdata,
                 put_mock_reqsdata, put_mock_ncr_data, put_mock_scandata, put_mock_accountscores_data):
        func()


def base_put_func(items, table, tablename):
    for item in items:
        table.put_item(Item=item)
    return {tablename: items}


def put_mock_accountsdata():
    return base_put_func(ACCOUNTS_DATA, accounts_table, 'accounts_table')


def del_mock_accountsdata():
    for data in ACCOUNTS_DATA:
        accounts_table.delete_item(Key={'accountId': data['accountId']})


def put_mock_userdata():
    return base_put_func(USER_DATA, user_table, 'user_table')


def put_mock_scandata():
    return base_put_func(SCAN_DATA, scans_table, 'scans_table')


def put_mock_reqsdata():
    return base_put_func(REQUIREMENTS_DATA, requirements_table, 'requirements_table')


def del_mock_scandata():
    for data in SCAN_DATA:
        scans_table.delete_item(
            Key={
                'scan': ScansTable.SCAN,
                'scanId': data['scanId'],
            },
        )


def del_mock_userdata():
    for data in USER_DATA:
        user_table.delete_item(
            Key={
                'email': data['email'],
            },
        )

def del_mock_reqsdata():
    for data in REQUIREMENTS_DATA:
        requirements_table.delete_item(
            Key={
                'requirementId': data['requirementId'],
            },
        )


def put_mock_scoresdata():
    return base_put_func(SCORES_DATA, scores_table, 'scores_table')


def put_mock_ncr_data():
    return base_put_func(NCR_DATA, ncr_table, 'ncr_table')


def put_mock_accountscores_data():
    # AccountScores: fields: accountId, date, score object (weight, score)
    return base_put_func(ACCOUNT_SCORES_DATA, account_scores_table, 'account_scores_table')
