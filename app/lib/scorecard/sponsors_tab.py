from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.formatting.rule import ColorScaleRule

from .generic_formatter import Formatter, Header
from .generic_tab import create_tab

def create_sponsors_tab(worksheet: Worksheet, rows: list):
    """
    Function to specifically create the executive sponsors worksheet. Modified passed in workbook.

    Parameters:
    worksheet (Worksheet): The worksheet to modify.
    rows (list): Accounts to be dropped into the worksheet.
    """

    formatting = Formatter(
        title='Sponsor List',
        freeze='A2',
        headers=[
            Header(header_text='Executive sponsor', width=42, key=['executiveSponsor']),
            Header(header_text='Number of accounts', width=19, key=['accountCount']),
            Header(
                header_text='Accounts total score',
                width=19,
                key=['sumOfScores'],
                conditional_formatting=ColorScaleRule(start_type='num', start_value=0, start_color='92D002', end_type='max', end_color='FF0000')
            ),
        ],
        excel_filter=True,
    )

    create_tab(worksheet, rows, formatting)

    return worksheet
