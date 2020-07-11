from typing import List

class Header():
    def __init__(self, header_text, width, key, sort=False, conditional_formatting=None):
        self.header_text = header_text
        self.width = width
        self.key = key
        self.sort = sort
        self.conditional_formatting = conditional_formatting


    def get_value(self, row: dict) -> str:
        """
        The header object defines a method to get the value for a given row.

        Default implementation allows the key attribute to specify an array of potential key paths to get the value from the row

        Parameters:
        row (dict): The row which is being rendered.

        Returns:
        str: The found value from the row for this cell.
        """

        for key in self.key:
            keys = key.split('.')
            value = get_value_by_path(row, keys)
            if value != '':
                return value
        return ''

def get_value_by_path(dictionary: dict, keys: list):
    for key in keys:
        if isinstance(dictionary, dict):
            dictionary = dictionary.get(key, '')
        else:
            return ''
    return dictionary



class Formatter():
    def __init__(self, title, freeze, headers: List[Header], excel_filter=False):
        self.title = title
        self.freeze = freeze
        self.excel_filter = excel_filter
        self.headers = headers

    def format_resource(self, row: dict) -> list:
        """Extract fields from row record based on headers"""

        output = []
        for header in self.get_headers():
            output.append(header.get_value(row))

        return output

    def get_header_names(self):
        return [header.header_text for header in self.get_headers()]

    def get_headers(self):
        return self.headers
