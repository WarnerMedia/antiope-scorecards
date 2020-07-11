from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.formatting.rule import ColorScaleRule
from .generic_formatter import Formatter, Header
from .generic_tab import create_tab


def create_accounts_tab(worksheet: Worksheet, rows: list):
    """
    Function to specifically create the Non Compliant Resource worksheet. Modified passed in workbook.

    Parameters:
    worksheet (Worksheet): The worksheet to modify.
    rows (list): Accounts to be dropped into the worksheet.
    """

    formatting = Formatter(
        title='Accounts List',
        freeze='A2',
        headers=[
            Header(header_text='Account Name', width=42, key=['account_name', 'accountId']),
            Header(header_text='Account ID', width=14, key=['accountId']),
            Header(
                header_text='Score',
                width=9,
                key=['score'],
                conditional_formatting=ColorScaleRule(start_type='num', start_value=0, start_color='92D002', end_type='max', end_color='FF0000')
                ),
        ],
        excel_filter=True,
    )

    create_tab(worksheet, rows, formatting)

    return worksheet
