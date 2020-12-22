import requests 
from requests.exceptions import *

from core.helpers.func import *
from requests_html import HTMLSession, HTMLResponse

requests.packages.urllib3.disable_warnings()


class Request(HTMLSession):
    """
    请求处理类
    """

    # session = {}
    def save_to_file(self, url, path):
        response = self.get(url, stream=True)
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        return response

    @staticmethod
    def _handle_response(response, **kwargs) -> HTMLResponse:
        """
        扩充 response
        :param response:
        :param kwargs:
        :return:
        """
        response = HTMLSession._handle_response(response, **kwargs)
        expand_class(response, 'json', Request.json)
        return response

    def add_response_hook(self, hook):
        hooks = self.hooks['response']
        if not isinstance(hooks, list):
            hooks = [hooks]
        hooks.append(hook)
        self.hooks['response'] = hooks
        return self

    def json(self, default={}):
        """
        重写 json 方法，拦截错误
        :return:
        """
        from core.app import Dict
        try:
            result = self.old_json()
            return Dict(result)
        except:
            return Dict(default)

    def request(self, *args, **kwargs):  # 拦截所有错误
        try:
            if not 'timeout' in kwargs:
                from core.config import Config
                kwargs['timeout'] = Config().TIME_OUT_OF_REQUEST
            response = super().request(*args, **kwargs)
            return response
        except RequestException as e:
            from core.log.common_log import CommonLog
            if e.response:
                response = e.response
            else:
                response = HTMLResponse(HTMLSession)
                # response.status_code = 500
                expand_class(response, 'json', Request.json)
            response.reason = response.reason if response.reason else CommonLog.MESSAGE_RESPONSE_EMPTY_ERROR
            return response

    def cdn_request(self, url: str, cdn=None, method='GET', **kwargs):
        #from core.helpers.api import HOST_URL_OF_12306
        #from core.helpers.cdn import Cdn
        #if not cdn: cdn = Cdn.get_cdn()
        #url = url.replace(HOST_URL_OF_12306, cdn)

        return self.request(method, url, headers={'Host': HOST_URL_OF_12306}, verify=False, **kwargs)

    def dump_cookies(self):
        cookies = []
        for _, item in self.cookies._cookies.items():
            for _, urls in item.items():
                for _, cookie in urls.items():
                    from http.cookiejar import Cookie
                    assert isinstance(cookie, Cookie)
                    if cookie.domain:
                        cookies.append({
                            'name': cookie.name,
                            'value': cookie.value,
                            'url': 'https://' + cookie.domain + cookie.path,
                        })
        return cookies
