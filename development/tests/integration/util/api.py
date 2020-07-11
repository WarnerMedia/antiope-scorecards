import os
import scorecard_sdk


def get_api(token) -> scorecard_sdk.DefaultApi:
    configuration = scorecard_sdk.Configuration(host=os.environ.get('API_ENDPOINT'), api_key={'Authorization': token})
    api = scorecard_sdk.DefaultApi(scorecard_sdk.ApiClient(configuration))
    return api
