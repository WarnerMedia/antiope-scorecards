import re
from copy import deepcopy
from typing import Set

import boto3
from botocore.exceptions import ClientError

from remediation.workers.worker_base import (IacCheckResponse, ParameterValidationResponse, RemediationResponse,
                                             ResourceValidationResponse, WorkerBase)


class SecurityGroupIngressWorker(WorkerBase):
    def __init__(self, event):
        # TODO Not sure what I think about having a constructor, consider moving to validate_input
        super().__init__(event)
        self.security_group_response = None
        self.security_group_id = self.get_security_group_id()
        self.region_name = self.ncr['region']

    def validate_input(self, ncr, remediation_parameters, requirement_based_parameters) -> ParameterValidationResponse:
        # TODO setup stuff here? (see constructor TODO)
        cidr_valid, cidr_message = self.validate_cidr_range(remediation_parameters['cidrRange'])
        description_valid, description_message = self.validate_description(remediation_parameters['description'])

        if cidr_valid and description_valid:
            return ParameterValidationResponse(valid=True, message='')
        else:
            return ParameterValidationResponse(valid=False, message=cidr_message or description_message)

    def iac_check(self, session, ncr, remediation_parameters, requirement_based_parameters) -> IacCheckResponse:
        """Returns True if resource was created by CloudFormation, else returns False"""
        self.set_security_group_response(session)
        to_evaluate = self.security_group_response['SecurityGroups'][0]
        if 'Tags' in to_evaluate:
            for tag in to_evaluate['Tags']:
                key = tag['Key']
                if key == 'aws:cloudformation:stack-name':
                    return IacCheckResponse(managed_by_iac=True, message=f'security group part of stack:{tag["Value"]}')
        return IacCheckResponse(managed_by_iac=False, message='')

    def resource_check(self, session, ncr, remediation_parameters, requirement_based_parameters) -> ResourceValidationResponse:
        """Confirm that resources can in fact be remediated now, which means there is a bad ingress rule present.
        Additionally, ports must match expected value and cannot be a range of ports."""
        valid_port = requirement_based_parameters['port']
        for ingress_rule in self.security_group_response['SecurityGroups'][0]['IpPermissions']:
            cidr_ips = [range_object['CidrIp'] for range_object in ingress_rule.get('IpRanges', []) if range_object]
            if '0.0.0.0/0' in cidr_ips:
                # NOTE that port checks are performed only after we know that the ingress_rule in question is a
                # bad rule that should be remediated. Other ingress rules may be present within the security group.
                if (from_port := ingress_rule['FromPort']) != (to_port := ingress_rule['ToPort']):
                    return ResourceValidationResponse(valid=False, message='Port range found. Must be single port.')
                if from_port != valid_port or to_port != valid_port:
                    return ResourceValidationResponse(valid=False,
                                                      message='Port mismatch between expected and observed')
                if ingress_rule.get('Ipv6Ranges', False):
                    return ResourceValidationResponse(valid=False,
                                                      message='rule involves ipv4 and ipv6 ranges. ipv6 not supported.')
                return ResourceValidationResponse(valid=True, message='')
        return ResourceValidationResponse(valid=False, message='Security group has no invalid rules')

    def remediate(self, session, ncr, remediation_parameters, requirement_based_parameters) -> RemediationResponse:
        """Replace 0.0.0.0/0 with user specified cidrRange on security group ingress rule."""
        new_description = remediation_parameters['description']
        ec2_resource = session.resource('ec2', region_name=self.region_name)
        security_group = ec2_resource.SecurityGroup(self.security_group_id)
        to_approve, to_revoke = self.modify_security_group(
            self.security_group_response, remediation_parameters['cidrRange'],
            requirement_based_parameters['port'], self.get_connection_protocols(), new_description)
        try:
            security_group.authorize_ingress(
                GroupName=self.security_group_response['SecurityGroups'][0]['GroupName'],
                IpPermissions=to_approve,
            )
            security_group.revoke_ingress(
                GroupName=self.security_group_response['SecurityGroups'][0]['GroupName'],
                IpPermissions=to_revoke,
            )
            return RemediationResponse(success=True, message='security group remediated')
        except ClientError:
            return RemediationResponse(success=False, message='error remediating security group')

    def set_security_group_response(self, session: boto3.session.Session) -> None:
        """caches response for usage with other methods"""
        ec2_client = session.client('ec2', region_name=self.region_name)
        self.security_group_response = ec2_client.describe_security_groups(
            GroupIds=[self.security_group_id]
        )

    def get_security_group_id(self) -> str:
        return self.ncr['resourceId']

    # icmp doesn't matter sense since we only care about a specific port (icmp doesn't use ports)
    def get_connection_protocols(self) -> Set:
        """returns set of valid connection protocols, either tcp or tcp + udp"""
        results = set()
        tcp_is_present = re.search(r'tcp', self.ncr['reason'].lower())
        udp_is_present = re.search(r'udp', self.ncr['reason'].lower())
        if tcp_is_present:
            results.add('tcp')
        if udp_is_present:
            results.add('udp')
        if not results:
            raise RuntimeError('no connection protocols found in "reason" property of ncr')
        return results

    @staticmethod
    def validate_cidr_range(cidr_range):
        if not isinstance(cidr_range, str):
            return (False, 'cidrRange must be a string')
        try:
            ip_address, subnet_mask = cidr_range.split('/')
            subnet_mask = int(subnet_mask)
            if not 0 <= subnet_mask <= 32:
                return (False, 'invalid subnet mask in cidr range')
            ip_address_parts = ip_address.split('.')
            if len(ip_address_parts) != 4:
                return (False, 'invalid ip address')
            if any(not 0 <= int(part) <= 255 for part in ip_address_parts):
                return (False, 'invalid ip address')
        except: # pylint: disable=bare-except
            return (False, 'invalid ip address')
        return (True, None)

    @staticmethod
    def validate_description(description):
        if not isinstance(description, str):
            return (False, 'description must be a string')
        return (True, None)

    @staticmethod
    def modify_security_group(response, new_cidr, port, connection_protocols, new_description):
        """returns tuple of rules to authorize and rules to revoke"""
        copied_security_groups = deepcopy(response['SecurityGroups'])  # avoid mutation of original response.
        rules_to_authorize = []
        rules_to_revoke = []
        ip_permissions = copied_security_groups[0]['IpPermissions']  # should be only one security group being modified
        for index, ingress_rule in enumerate(ip_permissions):
            # NOTE that port check is performed here because other rules involving other ports should be ignored.
            if ingress_rule['IpProtocol'] in connection_protocols and ingress_rule['FromPort'] == port:
                rules_to_authorize.append({
                    'FromPort': port,
                    'IpProtocol': copied_security_groups[0]['IpPermissions'][index]['IpProtocol'],
                    'IpRanges': [],
                    'Ipv6Ranges': [],
                    'PrefixListIds': deepcopy(copied_security_groups[0]['IpPermissions'][index]['PrefixListIds']),
                    'ToPort': port,
                    'UserIdGroupPairs': deepcopy(copied_security_groups[0]['IpPermissions'][index]['UserIdGroupPairs'])
                })
                rules_to_revoke.append(deepcopy(rules_to_authorize[index]))
                for range_object in ingress_rule['IpRanges']:
                    if range_object['CidrIp'] == '0.0.0.0/0':
                        rules_to_authorize[-1]['IpRanges'].append(
                            {
                                'CidrIp': new_cidr,
                                'Description': new_description
                            }
                        )
                        rules_to_revoke[-1]['IpRanges'].append(range_object)
                    else:
                        rules_to_revoke[-1]['IpRanges'].append(range_object)
        return rules_to_authorize, rules_to_revoke
