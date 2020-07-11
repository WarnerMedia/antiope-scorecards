from unittest.mock import patch

from botocore.stub import Stubber

from remediation.workers import worker_base
from remediation.workers.worker_base import (IacCheckResponse, ParameterValidationResponse, RemediationResponse,
                                             RemediationStatus, ResourceValidationResponse, WorkerBase)


class WorkerStubbedResponses(WorkerBase):
    def validate_input(self, ncr, remediation_parameters, requirement_based_parameters):
        return worker_base.ParameterValidationResponse(valid=True, message=None)

    def resource_check(self, session, ncr, remediation_parameters, requirement_based_parameters):
        return worker_base.ResourceValidationResponse(valid=True, message=None)

    def iac_check(self, session, ncr, remediation_parameters, requirement_based_parameters):
        return IacCheckResponse(managed_by_iac=False, message=None)

    def remediate(self, session, ncr, remediation_parameters, requirement_based_parameters):
        return worker_base.RemediationResponse(success=True, message='Done!!')

class PassingWorker(WorkerStubbedResponses):
    # don't actually need a credentials for the tests
    def get_readonly_session(self):
        return None
    def get_remediation_session(self):
        return None

class TestWorkerBase:
    def test_worker_logic_flow(self):
        event = {'ncr':''}
        worker = PassingWorker(event)
        with patch.object(worker, 'validate_input', wraps=worker.validate_input) as validate_input, \
             patch.object(worker, 'resource_check', wraps=worker.resource_check) as resource_check, \
             patch.object(worker, 'iac_check', wraps=worker.iac_check) as iac_check, \
             patch.object(worker, 'remediate', wraps=worker.remediate) as remediate:

            response = worker.run()

        validate_input.assert_called_once()
        iac_check.assert_called_once()
        resource_check.assert_called_once()
        remediate.assert_called_once()

        assert response == {
            'status': RemediationStatus.SUCCESS,
            'message': 'Done!!'
        }

    def test_worker_invalid_input(self):
        event = {'ncr': ''}
        worker = PassingWorker(event)

        with patch.object(worker, 'validate_input') as validate_input:
            validate_input.return_value = ParameterValidationResponse(valid=False, message='bad input')
            response = worker.run()

            assert response == {
                'status': RemediationStatus.VALIDATION_ERROR,
                'message': 'Invalid parameters: bad input'
            }

    def test_worker_resource_check(self):
        event = {'ncr': ''}
        worker = PassingWorker(event)

        with patch.object(worker, 'resource_check') as resource_check:
            resource_check.return_value = ResourceValidationResponse(valid=False, message='bad resources')
            response = worker.run()

            assert response == {
                'status': RemediationStatus.ERROR,
                'message': 'Resource is invalid, remediate manually: bad resources'
            }

    def test_worker_iac_check(self):
        event = {'ncr': '', 'overrideIacWarning': False}
        worker = PassingWorker(event)

        with patch.object(worker, 'iac_check') as iac_check:
            iac_check.return_value = IacCheckResponse(managed_by_iac=True, message='managed by cloudformation')
            response = worker.run()

            assert response == {
                'status': RemediationStatus.IAC_OVERRIDE_REQUIRED,
                'message': 'IAC override required: managed by cloudformation'
            }
            worker.iac_override = True
            response = worker.run()

            assert response == {
                'status': RemediationStatus.SUCCESS,
                'message': 'Done!!'
            }

    def test_worker_failed_remediation(self):
        event = {'ncr': ''}
        worker = PassingWorker(event)

        with patch.object(worker, 'remediate') as remediate:
            remediate.return_value = RemediationResponse(success=False, message='Error updating security group')
            response = worker.run()

            assert response == {
                'status': RemediationStatus.ERROR,
                'message': 'Error updating security group'
            }

    def test_worker_error(self):
        event = {'ncr': ''}
        worker = PassingWorker(event)

        with patch.object(worker, 'remediate') as remediate:
            remediate.side_effect = ModuleNotFoundError('Something bad happened')
            response = worker.run()

            assert response == {
                'status': RemediationStatus.ERROR,
                'message': 'Error during remediation'
            }

    def test_worker_readonly_role_error(self):
        event = {'ncr': ''}
        worker = PassingWorker(event)

        with patch.object(worker, 'get_readonly_session') as get_role:
            get_role.side_effect = SyntaxError('Something really bad happened')
            response = worker.run()

            assert response == {
                'status': RemediationStatus.ERROR,
                'message': 'Unable to assume read only role'
            }

    def test_worker_remediation_role_error(self):
        event = {'ncr': ''}
        worker = PassingWorker(event)

        with patch.object(worker, 'get_remediation_session') as get_role:
            get_role.side_effect = SyntaxError('Something really bad happened')
            response = worker.run()

            assert response == {
                'status': RemediationStatus.ERROR,
                'message': 'Unable to assume remediation role'
            }

    def test_worker_role_assumption(self):
        event = {
            'ncr':'',
            'readonlyRoleArn': 'arn:aws:iam:123123123123::role/test',
            'remediationRoleArn': 'arn:aws:iam:123123123123::role/test',
        }
        with Stubber(worker_base.sts_client) as stubber:
            stubber.add_response('assume_role', {
                'Credentials': {
                    'AccessKeyId':'AKIAFAKEFAKEFAK1',
                    'SecretAccessKey':'',
                    'SessionToken':'',
                    'Expiration': '2099-10-10'
                }
            })
            stubber.add_response('assume_role', {
                'Credentials': {
                    'AccessKeyId':'AKIAFAKEFAKEFAK2',
                    'SecretAccessKey':'',
                    'SessionToken':'',
                    'Expiration': '2099-10-10'
                }
            })
            worker = WorkerStubbedResponses(event)
            session = worker.get_readonly_session()
            assert session.get_credentials().access_key == 'AKIAFAKEFAKEFAK1'
            session = worker.get_remediation_session()
            assert session.get_credentials().access_key == 'AKIAFAKEFAKEFAK2'
