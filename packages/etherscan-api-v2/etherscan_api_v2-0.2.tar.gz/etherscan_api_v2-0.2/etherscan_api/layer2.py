from etherscan_api.base import BaseApi, EtherscanApiError


class Layer2ApiMixIn(BaseApi):
    def get_plasma_deposits(self, address: str, page: int = 1, offset: int = 0):
        if self.chain_id not in [137, 100, 199]:
            raise EtherscanApiError('This endpoint is only available for Polygon (137), Xdai (100) and BTTC(199)')
        return self._get_v2_api('account', 'txnbridge', params={'address': address, 'page': page, 'offset': offset})

    def get_deposit_txs(self, address: str, page: int = 1, offset: int = 0, sort: str = 'desc'):
        if self.chain_id not in [10, 42161]:
            raise EtherscanApiError('This endpoint is only available for the Arbitrum and Optimism stack chains.')
        return self._get_v2_api('account', 'getdeposittxs',
                                params={'address': address, 'page': page, 'offset': offset, 'sort': sort})

    def get_withdraw_txs(self, address: str, page: int = 1, offset: int = 0, sort: str = 'desc'):
        if self.chain_id not in [10, 42161]:
            raise EtherscanApiError('This endpoint is only available for the Arbitrum and Optimism stack chains.')
        return self._get_v2_api('account', 'getwithdrawaltxs',
                                params={'address': address, 'page': page, 'offset': offset, 'sort': sort})
