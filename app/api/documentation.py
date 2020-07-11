import json
from string import Template

from lib.lambda_decorator.decorator import api_decorator


@api_decorator
def documentation_handler(event, context):
    spec = json.load(open('./swagger.packaged.json', 'r'))
    title = spec['info']['title']

    template = Template(open('./assets/swagger-template.html').read())
    result = template.safe_substitute(title=title, spec=json.dumps(spec))
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html'
        },
        'body': result,
    }
