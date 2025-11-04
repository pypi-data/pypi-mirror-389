from daaskit.sdk.config import CONFIG
from daaskit.sdk.utils import request as sdk_request

class ExtApi:
    def __init__(self, request: sdk_request.Request):
        self.request = request
    
    def call(self, id: str, param: any = None, stdRetData: bool = True) -> sdk_request.Response:
        resp = self.request.do(sdk_request.Options(
            host=CONFIG.extend_api_host,
            method='POST',
            url='/api/v1/meta_api/call'
        ).setJsonData({
            'id': id,
            'param': param
        }))
        if not stdRetData or resp.err:
            return resp
        respData, err = resp.data()
        if err:
            return sdk_request.newResponseError(err)
        if respData and isinstance(respData, dict):
            code = respData.get('code', 0)
            msg = respData.get('msg', None)
            data = respData.get('data', None)
            if code != 200 and msg:
                return sdk_request.newResponseError(Exception(f'{code} {msg}'))
            elif code == 200:
                resp.setResp(data, None)
        return resp