from typing import List

from etherscan_api.base import BaseApi


class TokenApiMixIn(BaseApi):
    # ✅
    def get_token_supply(self, contract_address: str) -> int:
        """Token 总供应量"""
        total_supply = self._get_v2_api('stats', 'tokensupply', {"contractaddress": contract_address})
        return int(total_supply)

    # ✅
    def get_token_balance(self, contract_address: str, address: str, tag: str = "latest") -> int:
        balance = self._get_v2_api('account', 'tokenbalance',
                                   {'contractaddress': contract_address, 'address': address, 'tag': tag})
        return int(balance)


class TokenExtraApiMixIn(BaseApi):
    def get_token_holders(self, contract_address: str) -> List[str]:
        data = self.get_token_tx_list(contract_address=contract_address)
        holders = set()
        for tx in data:
            holders.add(tx["from"])
            holders.add(tx["to"])
        return list(holders)

    def get_token_holders_and_balance(self, contract_address: str) -> List[tuple]:
        _holders = self.get_token_holders(contract_address)
        holders = []
        for addr in _holders:
            balance = self.get_token_balance(contract_address, addr)
            holders.append((addr, balance))
        return holders

    def get_token_valid_holders(self, contract_address: str):
        holders = self.get_token_holders_and_balance(contract_address)
        return [i for i in holders if i[1] > 0]

    def get_token_top_holders(self, contract_address: str, limit: int = 10):
        holders = self.get_token_holders_and_balance(contract_address)
        sorted_holders = sorted(holders, key=lambda i: i[1])
        return sorted_holders[:limit]


class TokenProApiMixIn(BaseApi):
    # only pro user ❌
    def get_token_supply_history(self, contract_address: str, block_no: int) -> str:
        """Token 总供应量"""
        return self._get_v2_api('stats', 'tokensupplyhistory', {"contractaddress": contract_address,
                                                                "blockno": block_no})

    # only pro user ❌
    def get_token_balance_history(self, address: str, contract_address: str, block_no: int) -> str:
        """"""
        return self._get_v2_api('account', 'tokenbalancehistory', {"address": address,
                                                                   "contractaddress": contract_address,
                                                                   "blockno": block_no})

    # only pro user ❌
    def get_token_info(self, contract_address: str):
        return self._get_v2_api('token', 'tokeninfo', {"contractaddress": contract_address})

    # only pro user ❌
    def get_token_top_holders(self, contract_address: str, offset: int = 0):
        return self._get_v2_api('token', 'topholders', {"contractaddress": contract_address,
                                                        "offset": offset})

    # only pro user ❌
    def get_token_holder_list(self, contract_address: str, page: int = 1, offset: int = 0):
        return self._get_v2_api('token', 'tokenholderlist', {"contractaddress": contract_address,
                                                             "page": page, "offset": offset})

    # only pro user ❌
    def get_token_holder_count(self, contract_address: str):
        return self._get_v2_api('token', 'tokenholdercount', {"contractaddress": contract_address})

    # only pro user ❌
    def get_address_erc20_token_balance(self, address: str, page: int = 1, offset: int = 0):
        return self._get_v2_api('token', 'addresstokenbalance', {"address": address, "page": page, "offset": offset})

    # only pro user ❌
    def get_address_erc721_token_balance(self, address: str, page: int = 1, offset: int = 0):
        return self._get_v2_api('token', 'addresstokennftbalance', {"address": address, "page": page, "offset": offset})

    # only pro user ❌
    def get_address_erc20_token_inventory(self, address: str, contract_address: str, page: int = 1, offset: int = 0):
        return self._get_v2_api('token', 'addresstokennftinventory',
                                {"address": address, "contractaddress": contract_address,
                                 "page": page, "offset": offset})
