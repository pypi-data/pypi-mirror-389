#!/usr/bin/python
# -*- coding: UTF-8 -*-
from typing import Any, Union, Tuple
import io, os, requests, json
from daaskit.sdk.log import logger

_DEFAULT_TIMEOUT = 20

class Options:
   """
    请求选项
    Attributes:
        method (str): HTTP方法, 如"GET", "POST"等。默认值为"GET"。
        url (str): 请求的URL路径, 不包含主机部分。
        host (str): 主机地址, 若url为完整URL则忽略此字段。
        header (dict): 请求头字典。
        data (any): 请求体数据, 可以是字符串、字节或FormData对象。
        login (bool): 是否需要登录验证, 默认为True。
        timeout (int): 请求超时时间, 单位为秒, 默认为20秒。
        json_resp (bool): 是否将响应解析为JSON格式, 默认为True。
   """
   def __init__(self, method: str = "GET", url: str = "", host: str = "", header: dict = None, data: any = None, login: bool = True, timeout: int = _DEFAULT_TIMEOUT, json_resp: bool = True):
      self.method = method
      self.url = url
      self.host = host
      self.header = header
      self.data = data
      self.login = login
      self.timeout = timeout if timeout > 0 else _DEFAULT_TIMEOUT
      self.json_resp = json_resp
   def getTimeout(self):
       if self.timeout > 0:
          return self.timeout
       return _DEFAULT_TIMEOUT
   def setJsonData(self, data: any, encoding: str = "utf-8") -> 'Options':
       try:
          self.data = json.dumps(data).encode(encoding = encoding)
       except Exception as e:
          logger.error(f"Error serializing JSON data: {e}")
       if not self.header:
           self.header = {}
       self.header["Content-Type"] = "application/json"
       return self

class FormData:
    def __init__(self):
        self._fields = {}
        self._files_to_close = []

    def append(self, name: str, value, content_type: str = None) -> bool: # 返回布尔值指示成功或失败
        if not isinstance(name, str) or not name:
            # 对于这种基础错误, 通常还是抛出异常更合理, 因为name是方法的基础契约
            logger.error(f"Error: Field name must be a non-empty string. Got: {name}")
            return False

        converted_value = None
        if not isinstance(value, str):
            try:
                converted_value = str(value)
            except Exception as e:
                logger.error(f"Warning: Could not convert value '{value}' (type {type(value)}) to string for field '{name}': {e}")
                return False # 转换失败, 返回 False
        else:
            converted_value = value

        # 再次检查以防str()失败或返回非str
        if not isinstance(converted_value, str):
            logger.error(f"Warning: Value for field '{name}' could not be converted to string. Resulting type: {type(converted_value)}")
            return False # 最终不是字符串, 返回 False

        if content_type:
            self._fields[name] = (None, converted_value, content_type)
        else:
            self._fields[name] = (None, converted_value)
        return True # 成功添加

    def appendFile(self, name: str, file_path: str, filename: str = None, content_type: str = None) -> bool:
        if not isinstance(name, str) or not name:
            logger.error(f"Error: Field name must be a non-empty string. Got: {name}")
            return False
        if not os.path.exists(file_path):
            logger.error(f"Warning: File not found at: {file_path} for field '{name}'")
            return False

        try:
            file_obj = open(file_path, 'rb')
            self._files_to_close.append(file_obj)
        except IOError as e:
            logger.error(f"Warning: Could not open file '{file_path}' for field '{name}': {e}")
            return False

        if not filename:
            filename = os.path.basename(file_path)

        if content_type:
            self._fields[name] = (filename, file_obj, content_type)
        else:
            self._fields[name] = (filename, file_obj)
        return True

    def appendFileFromBytes(self, name: str, data: bytes, filename: str, content_type: str = None) -> bool:
        if not isinstance(name, str) or not name:
            print(f"Error: Field name must be a non-empty string. Got: {name}")
            return False
        if not isinstance(filename, str) or not filename:
            print(f"Warning: Filename for field '{name}' must be a non-empty string. Got: {filename}")
            return False

        processed_data = None
        if isinstance(data, str):
            try:
                processed_data = data.encode('utf-8') # 尝试编码为UTF-8字节
            except Exception as e:
                print(f"Warning: Could not encode string data for field '{name}' to bytes (UTF-8): {e}")
                return False
        elif isinstance(data, bytes):
            processed_data = data
        else:
            print(f"Warning: File data for field '{name}' must be bytes or string. Got: {type(data)}")
            return False

        # 再次检查以防编码失败或返回非bytes
        if not isinstance(processed_data, bytes):
            print(f"Warning: Data for field '{name}' could not be converted to bytes. Resulting type: {type(processed_data)}")
            return False

        file_obj = io.BytesIO(processed_data)

        if content_type:
            self._fields[name] = (filename, file_obj, content_type)
        else:
            self._fields[name] = (filename, file_obj)
        return True

    def export(self):
        return self._fields

    def close_files(self):
        for f_obj in self._files_to_close:
            try:
                f_obj.close()
            except Exception as e:
                logger.error(f"Warning: Error closing file {f_obj}: {e}")
        self._files_to_close.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_files()

class Response:
    def __init__(self, response: requests.Response = None, options: Options = None):
        self.status_code = response.status_code if response else -1
        self.response = response
        self.options = options
        self._data = response.content if response else None
        self._ret = None
        self._err = None
    def data(self) -> Tuple[Any, Union[Exception, None]]:
        if self._err:
            return None, self._err
        if self._ret:
            return self._ret, None
        return self._data, None
    def json(self) -> Tuple[Any, Union[Exception, None]]:
        if self._err or not self.data:
            return None, self._err
        if self.response:
            try:
                return self.response.json(), None
            except Exception as e:
                return None, e
        try:
            return json.loads(self._data.decode("utf-8")), None
        except Exception as e:
            return None, e
    def setResp(self, ret: any, err: Union[Exception, None]):
        self._ret = ret
        self._err = err
    def rewriteData(self, data: any):
        self._data = data
    @property
    def raw(self):
        return self._data
    @property
    def err(self):
        return self._err
    def __str__(self):
        if self._err or not self._data:
            return ""
        if self.response:
            return self.response.text
        return str(self._data)

def newResponseError(err: Exception) -> Response:
    resp = Response()
    resp.status_code = 500
    resp._err = err if isinstance(err, Exception) else Exception(str(err))
    return resp

class Request:
    def __init__(self, options: Options):
        self.host = options.host
        self.header = options.header
        self.timeout = options.getTimeout()
        self.before_request_callback = None
        self.before_response_callback = None
    def setHost(self, host: str):
        self.host = host
        return self
    def fullUrl(self, url: str):
        if url.startswith("http"):
            return url
        return f"{self.host}{url}"
    def do(self, options: Options) -> Response:
        try:
            return self._do(options)
        except Exception as e:
            logger.error(f"request error: {e}")
            return newResponseError(e)
    def _do(self, options: Options) -> Response:
        method = self.getMethod(options)
        url = self.getUrl(options)
        header = self.getHeader(options)
        timeout = self.getTimeout(options)
        data = options.data
        files = None

        # 处理 FormData 类型的 data, 支持文件上传
        if data and isinstance(data, FormData):
            with data:
                files = data.export()
            data = None

        req = { "method": method, "url": url, "headers": header, "data": data, "files": files, "timeout": timeout }

        if self.before_request_callback:
            self.before_request_callback(req, options)

        response = requests.request(**req)
        resp = Response(response=response, options=options)
        if self.before_response_callback:
            self.before_response_callback(resp)
        return resp
    def getMethod(self, options: Options):
        if not options.method:
            return "GET"
        return options.method.upper()
    def getUrl(self, options: Options):
        url = options.url
        if url.startswith("http"):
            return url
        host = self.host
        if options.host:
            host = options.host
        return f"{host}{url}"
    def getHeader(self, options: Options):
        header = {}
        if self.header:
            header.update(self.header)
        if options.header:
            header.update(options.header)
        return header
    def getTimeout(self, options: Options):
        if options.timeout and options.timeout > 0:
            return options.timeout
        return self.timeout
