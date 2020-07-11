"""Module concerned with the 'Replace 0.0.0.0/0 with user specified CIDR on security group ingress rule'
Worker function"""
from remediation.workers.security_group_ingress import SecurityGroupIngressWorker


def security_group_ingress_handler(event, context):
    """
    Replace 0.0.0.0/0 with user specified CIDR on security group ingress rule.
    This handler corresponds to the "remediation function" mentioned within
    page 31 of the detailed design doc.
    This handler performs the remediation, which in this case is modifying
    an ingress rule.
    :param event: {
  "body": {
    "remediationParameters": {
      "CIDR": string,
      "SourceSecurityGroupId": string
    },
    "overrideIacWarning": bool,
    "readonly_role_arn": string,
    "role_session_name": string,
    "remediation_arn": string
  },
}
    :param context:
    :return:
    """
    # instantiate the worker class
    worker = SecurityGroupIngressWorker(event)
    return worker.run()
