#!/usr/bin/python
# -*- coding: UTF-8 -*-
from http import HTTPStatus
import json
from typing import Dict, Union

from daaskit.sdk import util
from daaskit.sdk.log import logger
from daaskit.sdk.utils import request as sdk_request
from daaskit.sdk.config import CONFIG

from daaskit.sdk.api_modules import system as system_api
from daaskit.sdk.api_modules import ext_api

_EXT_API_INDEXES = util.get_env('ENV_EXT_API_INDEXES')

class _Data:
    def __init__(self, initial_data=None):
        if isinstance(initial_data, dict):
            self.update(initial_data)

    def setData(self, key_path: str, value):
        parts = key_path.split('.')
        current_node = self
        
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                setattr(current_node, part, value)
            else:
                if hasattr(current_node, part):
                    next_node = getattr(current_node, part)
                    if not isinstance(next_node, _Data):
                        new_data_obj = _Data()
                        setattr(current_node, part, new_data_obj)
                        current_node = new_data_obj
                    else:
                        current_node = next_node
                else:
                    new_data_obj = _Data()
                    setattr(current_node, part, new_data_obj)
                    current_node = new_data_obj
    def update(self, data_dict: dict):
        if not isinstance(data_dict, dict):
            logger.warning('Update data failed: input is not a dictionary.')
            return
        
        for key_path, value in data_dict.items():
            self.setData(key_path, value)

    def __str__(self):
        return str(self.__dict__)

class Apis:
    def __init__(self, host: str = CONFIG.backend_host, account: str = CONFIG.admin_name, password: str = CONFIG.admin_pwd, org_domain: str = CONFIG.org_domain):
        self._options = _Data({ 'account': account, 'password': password, 'org_domain': org_domain, 'token': None })
        self._request = sdk_request.Request(sdk_request.Options(host=host))
        self._request.before_request_callback = self.before_request_callback
        self._request.before_response_callback = self.before_response_callback

        self.system = _Data({
            'user': system_api.UserApi(self._request),
            'ext_api': ext_api.ExtApi(self._request)
        })

        self.exts = _Data()
        self.__init_ext_caller()

    def login(self):
        resp = self.system.user.login(self._options.account, self._options.password)
        respData, err = resp.data()
        if err:
            logger.error(f'Login failed: {err}')
            raise err
        if not respData:
            logger.error('Login failed: Empty response.')
            raise Exception('Empty response')
        token = respData.get('token', '')
        if not token:
            logger.error('Login failed: Token not found in response.')
            raise Exception('Token not found in response')
        self._options.update({ 'token': token, 'user': respData, 'is_login': True })
        logger.info('Login successful.')
        return self

    def logout(self):
        if not self._options.token:
            logger.info('No active token, logout skipped.')
            return
        self.setToken(None)
        logger.info('Logged out, token cleared.')
        if not self.isLogin():
            return
        _is_login = False
        self._options.setData('is_login', _is_login)
        self.system.user.logout()

    @property
    def user(self) -> Union[Dict, None]:
        return self._options.user if hasattr(self._options, 'user') else None
    
    def isLogin(self) -> bool:
        return self._options.is_login

    def getHost(self) -> str:
        return self._request.host

    def getToken(self) -> str:
        return self._options.token

    def getOrgDomain(self) -> str:
        return self._options.org_domain

    def setHost(self, host: str):
        self._request.setHost(host)
        logger.info(f'Request host set to: {host}')
        return self

    def setToken(self, token: str):
        self._options.setData('token', token)
        logger.info('Token set successfully.')
        return self

    def setOrgDomain(self, domain: str):
        self._options.setData('org_domain', domain)
        logger.info(f'Organization domain set to: {self._options.org_domain}')
        return self

    def setExtCaller(self, key_path: str, id: str):
        def _setCaller(param: any = None, stdRetData: bool = True):
            return self.system.ext_api.call(id=id, param=param, stdRetData=stdRetData)
        self.exts.setData(key_path, _setCaller)
        return self

    def updateExtCaller(self, data: dict):
        for key_path, id in data.items():
            self.setExtCaller(key_path, id)
        return self

    def __init_ext_caller(self):
        try:
            if not _EXT_API_INDEXES:
                logger.info('none')
                return
            if _EXT_API_INDEXES.startswith('{'):
                self.updateExtCaller(json.loads(_EXT_API_INDEXES.encode('utf-8')))
                return
            else:
                for item in _EXT_API_INDEXES.split(';'):
                    if not item:
                        continue
                    try:
                        parts = item.split(':')
                        if len(parts) != 2:
                            continue
                        key_path = parts[0].strip()
                        id = parts[1].strip()
                        if not key_path or not id:
                            continue
                        self.setExtCaller(key_path, id)
                    except Exception as e:
                        logger.error(f'Failed to set caller for item "{item}": {e}')
        except Exception as e:
            logger.error(f'Failed to init caller from ENV_EXT_API_INDEXES: {e}')

    def before_request_callback(self, request: dict, options: sdk_request.Options):
        if not options.login:
            return
        if not self._options.token:
            self.login()
        header = request.get('headers', {})
        header['token'] = self._options.token
        header['org-domain'] = self._options.org_domain
        request['headers'] = header

    def before_response_callback(self, response: sdk_request.Response):
        if response.err or not response.options.json_resp:
            return
        result, _ = response.json()
        if not result:
            return
        code = result.get('code', 0)
        msg = result.get('msg', None)
        data = result.get('data', None)
        if code != 200 and msg:
            response.setResp(None, Exception(f'{code} {msg}'))
        elif response.status_code >= 400 and response.status_code < 500:
            response.setResp(None, Exception(f'{response.status_code} {HTTPStatus(response.status_code).phrase}'))
        elif code == 200:
            response.rewriteData(data)
        elif response.status_code >= 500 and response.status_code < 600:
            response.setResp(None, Exception(f'{response.status_code} {HTTPStatus(response.status_code).phrase}'))

_apis_map: Dict[str, Apis] = {}

def default() -> Apis:
    if CONFIG.org_domain not in _apis_map:
        _apis_map[CONFIG.org_domain] = Apis()
    return _apis_map.get(CONFIG.org_domain)

def get(org_domain: str, **kwargs) -> Apis:
    if org_domain not in _apis_map:
        _apis_map[org_domain] = Apis(org_domain=org_domain, **kwargs)
    return _apis_map.get(org_domain)

def cleanup():
    global _apis_map
    if not _apis_map:
        return
    for apis in _apis_map.values():
        apis.logout()
    _apis_map.clear()
    logger.info('All API sessions have been cleaned up.')