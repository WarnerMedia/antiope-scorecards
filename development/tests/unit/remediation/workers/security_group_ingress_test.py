from unittest.mock import Mock

from botocore.exceptions import ClientError

from remediation.workers.security_group_ingress import SecurityGroupIngressWorker
from remediation.workers.worker_base import (IacCheckResponse, RemediationResponse, RemediationStatus,
                                             ResourceValidationResponse, WorkerResponse)


class TestSGIngressValidation():
    def test_validate_input(self):
        sg_worker = SecurityGroupIngressWorker({'ncr': {'resourceId': 'sg-1234', 'region': 'us-east-1'}})
        result = sg_worker.validate_input('', {'cidrRange': '1.2.3.4/28', 'description': 'vpn endpoint'}, {})
        assert result == (True, '')

        result = sg_worker.validate_input('', {'cidrRange': '1.2.3.4/28', 'description': 123}, {})
        assert result == (False, 'description must be a string')

    def test_valid_cidr(self):
        valid, _ = SecurityGroupIngressWorker.validate_cidr_range('1.2.3.4/28')
        assert valid is True

    def test_invalid_cidr_non_string(self):
        valid, _ = SecurityGroupIngressWorker.validate_cidr_range(123)
        assert valid is False

    def test_invalid_cidr_subnet(self):
        valid, _ = SecurityGroupIngressWorker.validate_cidr_range('1.2.3.4/33')
        assert valid is False
        valid, _ = SecurityGroupIngressWorker.validate_cidr_range('1.2.3.4/asdf')
        assert valid is False
        valid, _ = SecurityGroupIngressWorker.validate_cidr_range('1.2.3.4/-1')
        assert valid is False

    def test_invalid_base_ip_address(self):
        valid, _ = SecurityGroupIngressWorker.validate_cidr_range('1.2.3.4.5/28')
        assert valid is False
        valid, _ = SecurityGroupIngressWorker.validate_cidr_range('100.100.100.300/28')
        assert valid is False
        valid, _ = SecurityGroupIngressWorker.validate_cidr_range('100.100/28')
        assert valid is False
        valid, _ = SecurityGroupIngressWorker.validate_cidr_range('100.100/28')
        assert valid is False

    def test_valid_description(self):
        valid, _ = SecurityGroupIngressWorker.validate_description('vpn endpoint')
        assert valid is True

    def test_invalid_description(self):
        valid, _ = SecurityGroupIngressWorker.validate_cidr_range(123)
        assert valid is False


class TestSGIngressIacCheck:
    def test_is_iac(self):
        sg_worker = SecurityGroupIngressWorker({'ncr': {'resourceId': 'sg-1234', 'region': 'us-east-1'}})
        sg_worker.set_security_group_response = Mock()
        sg_worker.security_group_response = {
            'SecurityGroups': [
                {
                    'Tags': [
                        {
                            'Key': 'aws:cloudformation:stack-name',
                            'Value': 'foo'
                        }
                    ]
                }
            ]
        }
        response = sg_worker.iac_check(Mock(), Mock(), Mock(), Mock())
        assert response == IacCheckResponse(managed_by_iac=True, message='security group part of stack:foo')

    def test_is_not_iac(self):
        sg_worker = SecurityGroupIngressWorker({'ncr': {'resourceId': 'sg-1234', 'region': 'us-east-1'}})
        sg_worker.set_security_group_response = Mock()
        sg_worker.security_group_response = {
            'SecurityGroups': [
                {
                    'Tags': []
                }
            ]
        }
        response = sg_worker.iac_check(Mock(), Mock(), Mock(), Mock())
        assert response == IacCheckResponse(managed_by_iac=False, message='')


class TestSGIngressResourceCheck:
    def test_bad_rule_present(self):
        """bad rule SHOULD be present"""
        sg_worker = SecurityGroupIngressWorker({'ncr': {'resourceId': 'sg-1234', 'region': 'us-east-1'}})
        sg_worker.security_group_response = {
            'SecurityGroups': [
                {
                    'IpPermissions': [
                        {
                            'FromPort': 22,
                            'IpRanges': [
                                {
                                    'CidrIp': '0.0.0.0/0'
                                }
                            ],
                            'ToPort': 22
                        }
                    ]
                }
            ]
        }
        response = sg_worker.resource_check(Mock(), Mock(), Mock(), {
            'port': 22
        })
        assert response == ResourceValidationResponse(valid=True, message='')

    def test_bad_rule_not_present(self):
        sg_worker = SecurityGroupIngressWorker({'ncr': {'resourceId': 'sg-1234', 'region': 'us-east-1'}})
        sg_worker.security_group_response = {
            'SecurityGroups': [
                {
                    'IpPermissions': [
                        {
                            'FromPort': 22,
                            'IpRanges': [
                                {
                                    'CidrIp': '5.13.3.6/30'
                                }
                            ],
                            'ToPort': 22
                        }
                    ]
                }
            ]
        }
        response = sg_worker.resource_check(Mock(), Mock(), Mock(), {
            'port': 22
        })
        assert response == ResourceValidationResponse(valid=False, message='Security group has no invalid rules')

    def test_ports_do_not_match(self):
        """sg port not equal to port specified in requirement_based_parameters"""
        sg_worker = SecurityGroupIngressWorker({'ncr': {'resourceId': 'sg-1234', 'region': 'us-east-1'}})
        sg_worker.security_group_response = {
            'SecurityGroups': [
                {
                    'IpPermissions': [
                        {
                            'FromPort': 22,
                            'IpRanges': [
                                {
                                    'CidrIp': '0.0.0.0/0'
                                }
                            ],
                            'ToPort': 22
                        }
                    ]
                }
            ]
        }
        response = sg_worker.resource_check(Mock(), Mock(), Mock(), {
            'port': 4000
        })
        assert response == ResourceValidationResponse(valid=False,
                                                      message='Port mismatch between expected and observed')

    def test_ports_are_range(self):
        """port ranges not supported. only single port is acceptable."""
        sg_worker = SecurityGroupIngressWorker({'ncr': {'resourceId': 'sg-1234', 'region': 'us-east-1'}})
        sg_worker.security_group_response = {
            'SecurityGroups': [
                {
                    'IpPermissions': [
                        {
                            'FromPort': 22,
                            'IpRanges': [
                                {
                                    'CidrIp': '0.0.0.0/0'
                                }
                            ],
                            'ToPort': 23
                        }
                    ]
                }
            ]
        }
        response = sg_worker.resource_check(Mock(), Mock(), Mock(), {
            'port': 22
        })
        assert response == ResourceValidationResponse(valid=False,
                                                      message='Port range found. Must be single port.')


class TestSGIngressRemediate:
    def test_success(self):
        ncr = {'ncr': {'resourceId': 'sg-1234', 'region': 'us-east-1'}}
        sg_worker = SecurityGroupIngressWorker(ncr)
        sg_worker.modify_security_group = Mock(return_value=('foo', 'bar'))
        sg_worker.get_connection_protocols = Mock()
        sg_worker.security_group_response = {
            'SecurityGroups': [
                {
                    'GroupName': 'biz',
                    'IpPermissions': [
                        {
                            'FromPort': 22,
                            'IpRanges': [
                                {
                                    'CidrIp': '0.0.0.0/0'
                                }
                            ],
                            'ToPort': 22
                        }
                    ]
                }
            ]
        }
        result = sg_worker.remediate(
            Mock(return_value=Mock()),
            ncr,
            {
                'cidrRange': '10.10.10.10/30',
                'description': 'here is a new description'
            },
            {
                'port': 22
            }
        )
        assert result == RemediationResponse(success=True, message='security group remediated')

    def test_fail(self):
        ncr = {'ncr': {'resourceId': 'sg-1234', 'region': 'us-east-1'}}
        sg_worker = SecurityGroupIngressWorker(ncr)
        sg_worker.modify_security_group = Mock(return_value=('foo', 'bar'))
        sg_worker.get_connection_protocols = Mock()
        sg_worker.security_group_response = {
            'SecurityGroups': [
                {
                    'GroupName': 'biz',
                    'IpPermissions': [
                        {
                            'FromPort': 22,
                            'IpRanges': [
                                {
                                    'CidrIp': '0.0.0.0/0'
                                }
                            ],
                            'ToPort': 22
                        }
                    ]
                }
            ]
        }
        result = sg_worker.remediate(
            MockBadSession(),
            ncr,
            {
                'cidrRange': '10.10.10.10/30',
                'description': 'here is a new description'
            },
            {
                'port': 22
            }
        )
        assert result == RemediationResponse(success=False, message='error remediating security group')


class TestSGIngressGetConnectionProtocols:
    def test_tcp(self):
        ncr = {'ncr': {'resourceId': 'sg-1234', 'region': 'us-east-1', 'reason': 'tcp open'}}
        sg_worker = SecurityGroupIngressWorker(ncr)
        assert sg_worker.get_connection_protocols() == {'tcp'}

    def test_tcp_and_udp(self):
        ncr = {'ncr': {'resourceId': 'sg-1234', 'region': 'us-east-1', 'reason': 'tcp and udp open'}}
        sg_worker = SecurityGroupIngressWorker(ncr)
        assert sg_worker.get_connection_protocols() == {'tcp', 'udp'}


class TestSGIngressModifySecurityGroups:
    def test_one_rule(self):
        authorize, revoke = SecurityGroupIngressWorker.modify_security_group(
            {
                'SecurityGroups': [
                    {
                        'GroupName': 'biz',
                        'IpPermissions': [
                            {
                                'FromPort': 22,
                                'IpProtocol': 'tcp',
                                'IpRanges': [
                                    {
                                        'CidrIp': '0.0.0.0/0'
                                    }
                                ],
                                'Ipv6Ranges': [],
                                'PrefixListIds': [],
                                'ToPort': 22,
                                'UserIdGroupPairs': []
                            }
                        ]
                    }
                ]
            },
            '10.10.10.10/30',
            22,
            {'tcp'},
            'baz'
        )

        assert authorize == [
            {
                'FromPort': 22,
                'IpProtocol': 'tcp',
                'IpRanges': [
                    {
                        'CidrIp': '10.10.10.10/30',
                        'Description': 'baz'
                    }
                ],
                'Ipv6Ranges': [],
                'PrefixListIds': [],
                'ToPort': 22,
                'UserIdGroupPairs': []
            }
        ]
        assert revoke == [
            {
                'FromPort': 22,
                'IpProtocol': 'tcp',
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    }
                ],
                'Ipv6Ranges': [],
                'PrefixListIds': [],
                'ToPort': 22,
                'UserIdGroupPairs': []
            }
        ]

    def test_two_rules(self):
        """one unrelated rule is added here"""
        authorize, revoke = SecurityGroupIngressWorker.modify_security_group(
            {
                'SecurityGroups': [
                    {
                        'GroupName': 'biz',
                        'IpPermissions': [
                            {
                                'FromPort': 22,
                                'IpProtocol': 'tcp',
                                'IpRanges': [
                                    {
                                        'CidrIp': '0.0.0.0/0'
                                    }
                                ],
                                'Ipv6Ranges': [],
                                'PrefixListIds': [],
                                'ToPort': 22,
                                'UserIdGroupPairs': []
                            },
                            {
                                'FromPort': 5000,
                                'IpProtocol': 'tcp',
                                'IpRanges': [
                                    {
                                        'CidrIp': '5.5.5.5/28'
                                    }
                                ],
                                'Ipv6Ranges': [],
                                'PrefixListIds': [],
                                'ToPort': 5000,
                                'UserIdGroupPairs': []
                            }
                        ]
                    }
                ]
            },
            '10.10.10.10/30',
            22,
            {'tcp'},
            'baz'
        )

        assert authorize == [
            {
                'FromPort': 22,
                'IpProtocol': 'tcp',
                'IpRanges': [
                    {
                        'CidrIp': '10.10.10.10/30',
                        'Description': 'baz'
                    }
                ],
                'Ipv6Ranges': [],
                'PrefixListIds': [],
                'ToPort': 22,
                'UserIdGroupPairs': []
            }
        ]
        assert revoke == [
            {
                'FromPort': 22,
                'IpProtocol': 'tcp',
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    }
                ],
                'Ipv6Ranges': [],
                'PrefixListIds': [],
                'ToPort': 22,
                'UserIdGroupPairs': []
            }
        ]

    def test_two_ranges(self):
        """one valid range, one problematic"""
        authorize, revoke = SecurityGroupIngressWorker.modify_security_group(
            {
                'SecurityGroups': [
                    {
                        'GroupName': 'biz',
                        'IpPermissions': [
                            {
                                'FromPort': 22,
                                'IpProtocol': 'tcp',
                                'IpRanges': [
                                    {
                                        'CidrIp': '0.0.0.0/0'
                                    },
                                    {
                                        'CidrIp': '5.6.7.8/30'
                                    }
                                ],
                                'Ipv6Ranges': [],
                                'PrefixListIds': [],
                                'ToPort': 22,
                                'UserIdGroupPairs': []
                            }
                        ]
                    }
                ]
            },
            '10.10.10.10/30',
            22,
            {'tcp'},
            'baz'
        )

        assert authorize == [
            {
                'FromPort': 22,
                'IpProtocol': 'tcp',
                'IpRanges': [
                    {
                        'CidrIp': '10.10.10.10/30',
                        'Description': 'baz'
                    }
                ],
                'Ipv6Ranges': [],
                'PrefixListIds': [],
                'ToPort': 22,
                'UserIdGroupPairs': []
            }
        ]
        assert revoke == [
            {
                'FromPort': 22,
                'IpProtocol': 'tcp',
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    },
                    {
                        'CidrIp': '5.6.7.8/30'
                    }
                ],
                'Ipv6Ranges': [],
                'PrefixListIds': [],
                'ToPort': 22,
                'UserIdGroupPairs': []
            }
        ]

    def test_two_protocols(self):
        """tcp and udp open"""
        authorize, revoke = SecurityGroupIngressWorker.modify_security_group(
            {
                'SecurityGroups': [
                    {
                        'GroupName': 'biz',
                        'IpPermissions': [
                            {
                                'FromPort': 22,
                                'IpProtocol': 'tcp',
                                'IpRanges': [
                                    {
                                        'CidrIp': '0.0.0.0/0'
                                    }
                                ],
                                'Ipv6Ranges': [],
                                'PrefixListIds': [],
                                'ToPort': 22,
                                'UserIdGroupPairs': []
                            },
                            {
                                'FromPort': 22,
                                'IpProtocol': 'udp',
                                'IpRanges': [
                                    {
                                        'CidrIp': '0.0.0.0/0'
                                    }
                                ],
                                'Ipv6Ranges': [],
                                'PrefixListIds': [],
                                'ToPort': 22,
                                'UserIdGroupPairs': []
                            }
                        ]
                    }
                ]
            },
            '10.10.10.10/30',
            22,
            {'tcp', 'udp'},
            'baz'
        )

        assert authorize == [
            {
                'FromPort': 22,
                'IpProtocol': 'tcp',
                'IpRanges': [
                    {
                        'CidrIp': '10.10.10.10/30',
                        'Description': 'baz'
                    }
                ],
                'Ipv6Ranges': [],
                'PrefixListIds': [],
                'ToPort': 22,
                'UserIdGroupPairs': []
            },
            {
                'FromPort': 22,
                'IpProtocol': 'udp',
                'IpRanges': [
                    {
                        'CidrIp': '10.10.10.10/30',
                        'Description': 'baz'
                    }
                ],
                'Ipv6Ranges': [],
                'PrefixListIds': [],
                'ToPort': 22,
                'UserIdGroupPairs': []
            }
        ]
        assert revoke == [
            {
                'FromPort': 22,
                'IpProtocol': 'tcp',
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    }
                ],
                'Ipv6Ranges': [],
                'PrefixListIds': [],
                'ToPort': 22,
                'UserIdGroupPairs': []
            },
            {
                'FromPort': 22,
                'IpProtocol': 'udp',
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    }
                ],
                'Ipv6Ranges': [],
                'PrefixListIds': [],
                'ToPort': 22,
                'UserIdGroupPairs': []
            }
        ]


class TestSGIngressRunSuccess:
    def test_run_success(self):
        event = {
            'ncr': {'resourceId': 'sg-1234', 'region': 'us-east-1', 'reason': 'tcp port 22 open'},
            'userEmail': 'foo@bar.com',
            'remediationRoleArn': 'biz',
            'readonlyRoleArn': 'baz',
            'overrideIacWarning': False,
            'requirementBasedParameters': {
                'port': 22
            },
            'remediationParameters': {
                'cidrRange': '10.10.10.10/30',
                'description': 'sample description'
            }
        }
        sg_worker = SecurityGroupIngressWorker(event)
        sg_worker.get_readonly_session = Mock(return_value=MockGoodSessionReadOnly())
        sg_worker.get_remediation_session = Mock(return_value=MockGoodSessionRemediate())
        result = sg_worker.run()
        assert result == WorkerResponse(status=RemediationStatus.SUCCESS, message='security group remediated')


class MockGoodSessionReadOnly(Mock):
    def client(self, *args, **kwargs):
        return MockGoodEc2Client()


class MockGoodEc2Client(Mock):
    def describe_security_groups(self, *args, **kwargs):
        return {
            'SecurityGroups': [
                {
                    'GroupName': 'biz',
                    'IpPermissions': [
                        {
                            'FromPort': 22,
                            'IpProtocol': 'tcp',
                            'IpRanges': [
                                {
                                    'CidrIp': '0.0.0.0/0'
                                }
                            ],
                            'Ipv6Ranges': [],
                            'PrefixListIds': [],
                            'ToPort': 22,
                            'UserIdGroupPairs': []
                        }
                    ]
                }
            ]
        }


class MockGoodSessionRemediate(Mock):
    def resource(self, *args, **kwargs):
        return MockGoodEc2Resource()


class MockGoodEc2Resource(Mock):
    def SecurityGroup(self, *args, **kwargs):
        return MockGoodSG()


class MockGoodSG(Mock):
    def authorize_ingress(self, *args, **kwargs):
        pass


class MockBadSession(Mock):
    def resource(self, *args, **kwargs):
        return MockBadEc2Resource()


class MockBadEc2Resource(Mock):
    def SecurityGroup(self, *args, **kwargs):
        return MockBadSG()


class MockBadSG(Mock):
    def authorize_ingress(self, *args, **kwargs):
        raise ClientError({}, 'AuthorizeSecurityGroupIngress')
