import requests
import time
import getpass
import json
import re
import os
import platform
from pathlib import Path
import pickle
from typing import Mapping, List
import logging


logger = logging.getLogger(__name__)


_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'
_API_ROOT_URL = 'https://pc-api.empower-retirement.com'

# Caching cookies from successful login session to avoid 2-factor verification in the future
_CACHE_PATH = os.path.join(os.getenv('LOCALAPPDATA'), 'PersonalCapitalApi', 'Cache') if platform.system() == 'Windows' else '~/.cache/personal_capital_api'
_CACHE_VERSION = 1


class PersonalCapital():
    def __init__(self, use_cookies_cache=True):
        self._csrf = None
        self._use_cookies_cache = use_cookies_cache
        self._last_server_change_id = -1

        cookies = None
        if use_cookies_cache:
            cookies = self._load_cookies_from_cache()
            if cookies is not None:
                logger.debug(f'Loaded cookies from cache: {cookies.items()}')

        self._init_session(cookies)

    def api_request(self, method, path, data={}) -> Mapping:
        response = self.session.request(
            method=method,
            url=os.path.join(_API_ROOT_URL, path.lstrip('/')),
            data={**data, "csrf": self._csrf, "apiClient": 'WEB', "lastServerChangeId": self._last_server_change_id})
        resp_txt = response.text

        is_json_resp = re.match('text/json|application/json', response.headers.get('content-type', ''))

        if (response.status_code != requests.codes.ok or not is_json_resp):
            logger.error(f'_api_request failed response: {resp_txt}')
            raise RuntimeError(f'Request for {path} {data} failed: {response.status_code} {response.headers}')

        json_res = json.loads(resp_txt)

        if json_res.get('spHeader', {}).get('success', False) is False:
            if json_res.get('spHeader', {}).get('errors', [{}])[0].get('code', None) == 201:
                self._csrf = None
                raise PersonalCapitalSessionExpiredException(f'Login session expired {json_res["spHeader"]}')
            raise RuntimeError(f'API request seems to have failed: {json_res["spHeader"]}')

        return json_res

    def is_logged_in(self) -> bool:
        if self._csrf is None:
            return False

        try:
            self.get_accounts()
            return True
        except PersonalCapitalSessionExpiredException:
            return False

    def refresh_last_server_change_id(self):
        resp = self.api_request('post', 'api/login/querySession')
        last_server_change_id = resp.get('spHeader', {}).get('SP_HEADER_VERSION', None)
        if last_server_change_id:
            self._last_server_change_id = last_server_change_id

    def get_transactions(self, start_date='2007-01-01', end_date='2030-01-01') -> List[Mapping]:
        resp = self.api_request('post',
                                path='/api/transaction/getUserTransactions',
                                data={'startDate': start_date, 'endDate': end_date})

        return resp['spData']['transactions']

    def get_accounts(self) -> Mapping:
        resp = self.api_request('post', '/api/newaccount/getAccounts2')

        return resp['spData']

    def login(self, email, password,
                 auth_method='sms',
                 get_two_factor_code_func=lambda: getpass.getpass("Enter 2 factor code: ")) -> 'PersonalCapital':
        """
        Log in to Personal Capital via api

        You should run this function interactively at least once so you can supply the 2 factor authentication
        code interactively. After successful login, the cookies cached to the OS specific setting path (see _CACHE_PATH),
        so the next run should not need to 2 factor authenticate again.
        """

        if auth_method not in ('sms'):
            raise ValueError(f'Auth method {auth_method} is not supported')

        auth_resp = self.session.post(os.path.join(_API_ROOT_URL, 'api/auth/multiauth/noauth/authenticate'), json={
            'deviceFingerPrint':'9076b6df374f42acda3bd466324cf735',
            'userAgent': _USER_AGENT,
            'language':'en-US',
            'hasLiedLanguages':False,
            'hasLiedResolution':False,
            'hasLiedOs':False,
            'hasLiedBrowser':False,
            'userName': email,
            'password': password,
            'flowName':'mfa',
            'accu':'MYERIRA'
        }).json()

        if 'destinationUrl' not in auth_resp:
            raise RuntimeError(f'Login auth request seems to have failed: {auth_resp}')

        auth_token_resp = self.session.post(
            os.path.join(_API_ROOT_URL, auth_resp['destinationUrl'].lstrip('/')),
            data={'idToken': auth_resp['idToken']}).json()
        self._csrf = auth_token_resp.get('spHeader', {}).get('csrf')

        if not auth_token_resp.get('spHeader', {}).get('success'):
            sms_challenge_resp = self.api_request('post', 'api/credential/challengeSmsFreemium', data={
                'challengeReason': 'DEVICE_AUTH',
                'challengeMethod': 'OP',
                'bindDevice': False
            })

            two_factor_code = get_two_factor_code_func()
            sms_resp = self.api_request('post', 'api/credential/authenticateSmsFreemium', data={
                'code': two_factor_code,
                'challengeReason': 'DEVICE_AUTH',
                'challengeMethod': 'OP',
                'bindDevice': False
            })

        self._email = email

        if self._use_cookies_cache:
            self._cache_cookies()

        self.refresh_last_server_change_id()

        return self

    def _load_cookies_from_cache(self):
        cache_file = Path(_CACHE_PATH).expanduser() / 'cached_cookies.pkl'

        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                cached = pickle.load(f)
            if cached['version'] == _CACHE_VERSION:
                return cached['cookies']

    def _cache_cookies(self):
        cache_dir = Path(_CACHE_PATH).expanduser()
        cache_dir.mkdir(exist_ok=True, parents=True)
        cache_file = cache_dir / 'cached_cookies.pkl'

        with open(cache_file, 'wb') as f:
            logger.info(f'Caching cookies to file {cache_file}')
            pickle.dump({
                'version': _CACHE_VERSION,
                'cookies': self.session.cookies,
                'email': self._email,
            }, f)

    def _init_session(self, cookies=None):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': _USER_AGENT})

        if cookies:
            self.session.cookies = cookies


class PersonalCapitalSessionExpiredException(RuntimeError):
    pass

