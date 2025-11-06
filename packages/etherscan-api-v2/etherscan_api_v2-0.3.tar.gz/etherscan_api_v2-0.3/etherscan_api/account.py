from typing import List, Dict

from etherscan_api.base import BaseApi


class AccountMixInApi(BaseApi):
    # ✅
    def get_balance(self, address: str, tag: str = "latest") -> str:
        return self._get_v2_api('account', 'balance', {"address": address, "tag": tag})

    # ✅
    def get_balances(self, addresses: List[str], tag: str = "latest") -> str:
        return self._get_v2_api('account', 'balancemulti', {"address": ','.join(addresses), "tag": tag})

    # ✅
    def get_tx_list(self, address: str = None, contract_address: str = None, start_block: int = 0,
                    end_block: int = 99999999,
                    sort: str = "desc") -> List[Dict]:
        params = {"startblock": start_block, "endblock": end_block, "sort": sort}
        if contract_address:
            params["contractaddress"] = contract_address
        else:
            params["address"] = address
        return self._get_v2_api('account', 'txlist', params)

    # ✅
    def get_internal_tx_list(self, address: str = None, tx_hash: str = None, start_block: int = 0,
                             end_block: int = 99999999,
                             page: int = 1, offset: int = 0, sort: str = "desc") -> List[Dict]:
        if tx_hash:
            params = {"txhash": tx_hash}
        else:
            params = {"startblock": start_block, "endblock": end_block, "page": page, "offset": offset, "sort": sort}

            if address:
                params["address"] = address

        return self._get_v2_api('account', 'txlistinternal', params)

    # ✅
    def get_token_tx_list(self, address: str = None, contract_address: str = None, start_block: int = 0,
                          end_block: int = 99999999,
                          sort: str = "desc") -> List[Dict]:
        params = {"startblock": start_block, "endblock": end_block, "sort": sort}
        if contract_address:
            params["contractaddress"] = contract_address
        else:
            params["address"] = address
        return self._get_v2_api('account', 'tokentx', params)

    # ✅
    def get_token_nft_tx_list(self, address: str = None, contract_address: str = None, start_block: int = 0,
                              end_block: int = 99999999,
                              sort: str = "desc") -> List[Dict]:
        params = {"startblock": start_block, "endblock": end_block, "sort": sort}
        if contract_address:
            params["contractaddress"] = contract_address
        else:
            params["address"] = address
        return self._get_v2_api('account', 'tokennfttx', params)

    # ✅
    def get_token_1155_tx_list(self, address: str = None, contract_address: str = None, start_block: int = 0,
                               end_block: int = 99999999,
                               sort: str = "desc") -> List[Dict]:
        params = {"startblock": start_block, "endblock": end_block, "sort": sort}
        if contract_address:
            params["contractaddress"] = contract_address
        else:
            params["address"] = address
        return self._get_v2_api('account', 'token1155tx', params)

    # ✅
    def get_mined_blocks(self, address: str, block_type: str = "blocks", page: int = 0, offset: int = 0) -> List[Dict]:
        return self._get_v2_api('account', 'getminedblocks',
                                {"address": address, "blocktype": block_type, "page": page, "offset": offset})

    def get_beacon_withdrawal(self, address: str, start_block: int = 0, end_block: int = 99999999, page: int = 0,
                              offset: int = 0, sort: str = "desc") -> List[Dict]:
        return self._get_v2_api('account', 'txsBeaconWithdrawal',
                                {"address": address, "startblock": start_block, "endblock": end_block, "page": page,
                                 "offset": offset, "sort": sort})


class AccountProApiMixIn(BaseApi):
    # only pro user❌
    def get_balance_history(self, address: str, block_no: int) -> str:
        """"""
        return self._get_v2_api('account', 'balancehistory', {"address": address,
                                                              "blockno": block_no})
