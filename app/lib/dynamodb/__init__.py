import os

from .account_scores import AccountScoresTable
from .accounts import AccountsTable
from .audit import AuditTable
from .exclusions import ExclusionsTable
from .ncr import NCRTable
from .requirements import RequirementsTable
from .scans import ScansTable
from .scores import ScoresTable
from .config import ConfigTable
from .user import UserTable

account_scores_table = AccountScoresTable(os.getenv('ACCOUNT_SCORES_TABLE', 'accountScores-table'), ttl=60)
accounts_table = AccountsTable(os.getenv('ACCOUNTS_TABLE', 'accounts-table'))
audit_table = AuditTable(os.getenv('AUDIT_TABLE', 'audit-table'))
exclusions_table = ExclusionsTable(os.getenv('EXCLUSIONS_TABLE', 'exclusions-table'))
ncr_table = NCRTable(os.getenv('NCR_TABLE', 'nonCompliantResources-table'), ttl=30)
requirements_table = RequirementsTable(os.getenv('REQUIREMENTS_TABLE', 'requirements-table'))
scans_table = ScansTable(os.getenv('SCANS_TABLE', 'scans-table'), ttl=30)
scores_table = ScoresTable(os.getenv('SCORES_TABLE', 'scores-table'), ttl=30)
user_table = UserTable(os.getenv('USERS_TABLE', 'users-table'))
config_table = ConfigTable(os.getenv('CONFIG_TABLE', 'config-table'))
