from daaskit.sdk.utils import request as sdk_request
from daaskit.sdk.config import CONFIG
from daaskit.sdk.log import logger

class UserApi:
    def __init__(self, request: sdk_request.Request):
        self.request = request
    def login(self, account: str = CONFIG.admin_name, password: str = CONFIG.admin_pwd) -> sdk_request.Response:
        return self.request.do(sdk_request.Options(
            method='POST',
            url='/api/v1/sso/login',
            header={ 'Content-Type': 'application/json' },
            login=False
        ).setJsonData({
            'account': account,
            'password': password
        }))
    def logout(self) -> sdk_request.Response:
        return self.request.do(sdk_request.Options(
            method="POST",
            url="/api/v1/sso/logout",
            login=False
        ))