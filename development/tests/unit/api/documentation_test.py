import json
from unittest.mock import patch, Mock

from api.documentation import documentation_handler

class TestDocumentationHandler:
    @patch('json.load')
    @patch('builtins.open')
    def test_generate_documentation(self, mock_open: Mock, json_load: Mock):
        spec = {
            'openapi': '3.0.0',
            'info': {
                'title': 'myapi',
            },
        }
        template = '''$spec,$title'''
        mock_template_fp = Mock()
        mock_template_fp.read = Mock()
        mock_template_fp.read.return_value = template
        mock_open.side_effect = [
            Mock(),
            mock_template_fp,
        ]
        json_load.return_value = spec
        result = documentation_handler({}, {})
        assert result['body'] == '{},{}'.format(json.dumps(spec), spec['info']['title'])
