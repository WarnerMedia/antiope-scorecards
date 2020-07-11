class HttpException(Exception):
    """
    Base class for HTTP 4xx and 5xx client/server errors,
    vis-à-vis exception handling within the lambda decorator
    in this module.
    """
    def __init__(self, status, message, body=None):
        super().__init__()
        self.status = status
        self.message = message
        self.body = {'message': message}
        if body:
            self.body['body'] = body


class HttpNotFoundException(HttpException):
    """
    Resource not found
    """
    def __init__(self, message):
        super().__init__(404, message)


class HttpInvalidException(HttpException):
    """
    malformed request, etc
    """
    def __init__(self, message):
        super().__init__(400, message)


class HttpUnauthorizedException(HttpException):
    """
    auth failed or auth not provided
    """
    def __init__(self, message):
        super().__init__(401, message)


class HttpForbiddenException(HttpException):
    """
    user lacks necessary permissions, prohibited action, etc
    """
    def __init__(self, message):
        super().__init__(403, message)


class HttpServerErrorException(HttpException):
    """
    the code in question received a bad response from an
    upstream source
    """
    def __init__(self, message):
        super().__init__(502, message)


class HttpInvalidExclusionStateChange(HttpException):
    """
    invalid exclusion update status change
    """
    def __init__(self, current_exclusion: dict, update_request: dict, errors: dict):
        body = {
            'updateRequest': update_request,
            'errors': errors,
        }
        if current_exclusion:
            body['currentExclusion'] = current_exclusion
        super().__init__(403, 'Invalid exclusion state change', body=body)
