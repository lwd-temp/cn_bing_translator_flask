"""
Translator package.
"""


import json
import re
import time

import requests

from .exceptions import NoDataReceived, UnexpectedResponse, UnknownResponse, UnknownStatusCode


class Translator:
    def __init__(self, fromLang: str = "auto-detect", toLang: str = "en", agent: dict = {}, proxy: dict = {}, logger=None) -> None:
        self._fromLang = fromLang
        self._toLang = toLang
        self._ig = self._iig = self._key = self._token = None
        self._timeout = 0
        self._session = requests.Session()
        self._session.proxies = proxy
        if not agent:
            agent = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'}
        self._session.headers.update(agent)
        self._session.headers.update({'origin': 'https://cn.bing.com'})
        self._session.headers.update({'referer': 'https://cn.bing.com/translator/'})
        self._url = ''
        self._logger = logger
        # self._update_params()

    def _update_params(self):
        """
        update params IG, IID, token, key
        """
        self._session.cookies.clear()
        url = 'https://cn.bing.com/translator/'
        response = self._session.get(url=url)
        if self._logger:
            self._logger.debug('Update params.')
            self._logger.debug(f'Request url: {url}')
            self._logger.debug('Request type: get')
            self._logger.debug(f'Request headers: {self._session.headers}')
            self._logger.debug(f'Response status code: {response.status_code}')
            self._logger.debug(f'Response headers: {response.headers}')
            self._logger.debug(f'Response content: {response.text}')

        if response.status_code != 200:
            raise UnknownStatusCode
        iid = re.search(r'<div id="rich_tta" data-iid="(.*?)"', response.text)
        if iid:
            self._iid = iid.group(1)
        ig = re.search(',IG:"(.*?)",', response.text)
        if ig:
            self._ig = ig.group(1)
        match = re.search(r'params_AbusePreventionHelper = \[(\d+),"(.*?)",(\d+)\];', response.text)
        if match:
            self._key = match.group(1)
            self._token = match.group(2)
            self._timeout = int((time.time() - 600) * 1000) + int(match.group(3))
        if not (self._ig and self._iid and self._key and self._token and self._timeout):
            raise UnknownResponse
        if self._logger:
            self._logger.debug(f'iid: {self._iid}, ig: {self._ig}, key: {self._key}, token: {self._token}, timeout: {self._timeout}')
        self._url = f'https://cn.bing.com/ttranslatev3?isVertical=1&IG={self._ig}&IID={self._iid}'

    def process(self, text: str, fromLang: str = '', toLang: str = '') -> str:
        """
        translate text from origin language
        """
        if self._timeout < int(time.time() * 1000):
            self._ig = self._iig = self._key = self._token = None
            self._timeout = 0
            self._update_params()

        data = {
            '': '',
            'fromLang': fromLang if fromLang else self._fromLang,
            'text': f'{text}',
            'to': toLang if toLang else self._toLang,
            'token': self._token,
            'key': self._key,
            'tryFetchingGenderDebiasedTranslations': 'true'
        }
        response = self._session.post(url=self._url, data=data)

        if self._logger:
            self._logger.debug(f'Request url: {self._url}')
            self._logger.debug('Request type: post')
            self._logger.debug(f'Request headers: {self._session.headers}')
            self._logger.debug(f'Request data: {data}')
            self._logger.debug(f'Response status code: {response.status_code}')
            self._logger.debug(f'Response headers: {response.headers}')
            self._logger.debug(f'Response content: {response.text}')
        if response.status_code != 200:
            raise UnknownStatusCode
        try:
            content = json.loads(response.text)
        except:
            raise UnknownResponse
        if type(content) == dict:  # and content.get('statusCode'):
            # {"statusCode":205,"errorMessage":""}
            print('status code error, update params')
            self._ig = self._iig = self._key = self._token = None
            self._timeout = 0
            self._update_params()
            data = {
                '': '',
                'fromLang': fromLang if fromLang else self._fromLang,
                'text': f'{text}',
                'to': toLang if toLang else self._toLang,
                'token': self._token,
                'key': self._key,
                'tryFetchingGenderDebiasedTranslations': 'true'
            }
            response = self._session.post(url=self._url, data=data)
            if self._logger:
                self._logger.debug(f'Request url: {self._url}')
                self._logger.debug('Request type: post')
                self._logger.debug(f'Request headers: {self._session.headers}')
                self._logger.debug(f'Request data: {data}')
                self._logger.debug(f'Response status code: {response.status_code}')
                self._logger.debug(f'Response headers: {response.headers}')
                self._logger.debug(f'Response content: {response.text}')
            try:
                content = json.loads(response.text)
            except:
                raise UnknownResponse
            if response.status_code != 200:
                raise UnknownStatusCode
            if type(content) == dict:  # and content.get('statusCode'):
                raise UnexpectedResponse
        result = ''
        try:
            if type(content) == list and type(content[0] == dict):
                result = content[0].get('translations')[0].get('text')
            else:
                raise UnknownResponse
        except:
            raise UnknownResponse
        return result
