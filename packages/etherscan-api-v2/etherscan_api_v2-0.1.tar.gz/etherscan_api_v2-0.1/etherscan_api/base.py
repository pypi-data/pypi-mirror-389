import logging
import os
import time
from typing import Dict, Any

import requests

DEFAULT_HTTP_TIMEOUT = 10
DEFAULT_HTTP_RATE_LIMIT = 5
DEFAULT_HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, '
                                      'like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY') or '4843M1FG8DMMR6Q932S6RTYJGK25J4TSS2'

ETHERSCAN_BASE_URL = 'https://api.etherscan.io'


class EtherscanApiError(Exception):
    """"""


class BaseApi:
    def __init__(self, chain_id=1, api_key: str = None, timeout: int = 10, rate_limit: int = 5):
        self.chain_id = int(chain_id)
        self._base_url = ETHERSCAN_BASE_URL
        self.api_key = api_key or ETHERSCAN_API_KEY
        self.timeout = timeout
        self.rate_limit = rate_limit
        self._last_req = 0.0
        self._session = requests.session()
        self._session.headers = DEFAULT_HTTP_HEADERS

    def _throttle(self):
        """简单速率限制"""
        since_last = time.time() - self._last_req
        if since_last < 1 / self.rate_limit:
            time.sleep(1 / self.rate_limit - since_last)
        self._last_req = time.time()

    def _get(self, url, params=None) -> Dict:
        self._throttle()
        resp = self._session.get(self._base_url + url, params=params)
        resp.raise_for_status()
        return resp.json()

    def _get_v2_api(self, module, action, params: Dict[str, Any] = None) -> Any:
        params = params or {}
        params.setdefault("apikey", self.api_key)
        params.setdefault("chainid", self.chain_id)
        params.update({'module': module, 'action': action})
        # logging.debug(f'Get {self._base_url}/v2/api, params: {params}')
        data = self._get('/v2/api', params)
        logging.debug(f'Response data: {data}')
        if data.get("status") == "0" and data.get('message') != 'No transactions found':
            raise EtherscanApiError(f"{data.get('message')} : {data.get('result')}")
        if data.get('error'):
            raise EtherscanApiError(f"{data['error'].get('code')} : {data['error'].get('message')}")
        return data['result']
