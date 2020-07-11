"""
Base class for extending boto3's lambda and sts client functionality
"""
from abc import ABC, abstractmethod
from typing import NamedTuple, TypedDict

import boto3
from boto3.session import Session

from lib.logger import logger

sts_client = boto3.client('sts')


class WorkerEvent(TypedDict):
    remediationParameters: dict
    requirementBasedParameters: dict
    overrideIacWarning: bool
    readonlyRoleArn: str
    remediationRoleArn: str
    userEmail: str
    ncr: dict


class WorkerResponse(TypedDict):
    status: str
    message: str

class RemediationStatus:
    SUCCESS = 'success'
    ERROR = 'error'
    VALIDATION_ERROR = 'validationError'
    IAC_OVERRIDE_REQUIRED = 'iacOverrideRequired'

class ParameterValidationResponse(NamedTuple):
    valid: bool
    message: str

class ResourceValidationResponse(NamedTuple):
    valid: bool
    message: str

class IacCheckResponse(NamedTuple):
    managed_by_iac: bool
    message: str

class RemediationResponse(NamedTuple):
    success: bool
    message: str


class WorkerBase(ABC):
    def __init__(self, event: WorkerEvent):
        self.remediation_parameters = event.get('remediationParameters', {})
        self.requirement_based_parameters = event.get('requirementBasedParameters', {})
        self.iac_override = event.get('overrideIacWarning', False)
        self.readonly_arn = event.get('readonlyRoleArn', '')
        self.remediation_arn = event.get('remediationRoleArn', '')
        self.user_email = event.get('userEmail', '')
        self.role_session_name = f'remediation-{self.user_email}'
        self.ncr = event['ncr']  # this is the full contents of the ncr record.

    # The following four abstract methods are called in order. These should be implemented by worker subclasses

    @abstractmethod
    def validate_input(self, ncr, remediation_parameters, requirement_based_parameters) -> ParameterValidationResponse:
        """validate the remediation parameters (aka input) based on function specific requirements"""

    @abstractmethod
    def iac_check(self, session: Session, ncr, remediation_parameters, requirement_based_parameters) -> IacCheckResponse:
        """checks if the resource being remediated are managed by IAC (CloudFormation, terraform, etc)."""

    @abstractmethod
    def resource_check(self, session: Session, ncr, remediation_parameters, requirement_based_parameters) -> ResourceValidationResponse:
        """Confirm that resources can in fact be remediated now."""

    @abstractmethod
    def remediate(self, session: Session, ncr, remediation_parameters, requirement_based_parameters) -> RemediationResponse:
        """Modifies state of specified resources such that their non-compliant status is resolved."""

    def run(self) -> WorkerResponse:
        """This is called to perform the sequence of actions needed to perform the remediation"""
        logger.info('Starting remediation')
        try:
            input_validation_response = self.validate_input(self.ncr, self.remediation_parameters, self.requirement_based_parameters)
            if not input_validation_response.valid:
                return WorkerResponse(status=RemediationStatus.VALIDATION_ERROR, message='Invalid parameters: ' + input_validation_response.message)

            try:
                readonly_session = self.get_readonly_session()
            except: # pylint: disable=bare-except
                return WorkerResponse(status=RemediationStatus.ERROR, message='Unable to assume read only role')

            iac_check_response = self.iac_check(readonly_session, self.ncr, self.remediation_parameters, self.requirement_based_parameters)
            if iac_check_response.managed_by_iac and not self.iac_override:
                return WorkerResponse(status=RemediationStatus.IAC_OVERRIDE_REQUIRED, message='IAC override required: ' + iac_check_response.message)

            resource_check_response = self.resource_check(readonly_session, self.ncr, self.remediation_parameters, self.requirement_based_parameters)
            if not resource_check_response.valid:
                return WorkerResponse(status=RemediationStatus.ERROR, message='Resource is invalid, remediate manually: ' + resource_check_response.message)

            try:
                remediation_session = self.get_remediation_session()
            except: # pylint: disable=bare-except
                return WorkerResponse(status=RemediationStatus.ERROR, message='Unable to assume remediation role')

            remediation_response = self.remediate(remediation_session, self.ncr, self.remediation_parameters, self.requirement_based_parameters)
            if remediation_response.success:
                return WorkerResponse(status=RemediationStatus.SUCCESS, message=remediation_response.message)
            else:
                return WorkerResponse(status=RemediationStatus.ERROR, message=remediation_response.message)
        except: # pylint: disable=bare-except
            return WorkerResponse(status=RemediationStatus.ERROR, message='Error during remediation')

    def get_readonly_session(self) -> Session:
        """assumes read only role, then returns appropriate session"""
        readonly_credentials = sts_client.assume_role(
            RoleArn=self.readonly_arn,
            RoleSessionName=self.role_session_name
        )['Credentials']
        return boto3.session.Session(
            aws_access_key_id=readonly_credentials['AccessKeyId'],
            aws_secret_access_key=readonly_credentials['SecretAccessKey'],
            aws_session_token=readonly_credentials['SessionToken']
        )

    def get_remediation_session(self) -> Session:
        """assumes remediation role, then returns appropriate session"""
        remediation_credentials = sts_client.assume_role(
            RoleArn=self.remediation_arn,
            RoleSessionName=self.role_session_name
        )['Credentials']
        return boto3.session.Session(
            aws_access_key_id=remediation_credentials['AccessKeyId'],
            aws_secret_access_key=remediation_credentials['SecretAccessKey'],
            aws_session_token=remediation_credentials['SessionToken']
        )
