from typing import Dict

from etherscan_api.base import BaseApi


class ProxyApiMixIn(BaseApi):
    # Geth/Parity Proxy (节点代理)
    # ✅
    def get_block_number(self) -> int:  # hex str
        """最新区块号"""
        result_hex = self._get_v2_api('proxy', 'eth_blockNumber')
        return int(result_hex, 16)

    # ✅
    def get_block_by_number(self, number: str = "latest", boolean: bool = True) -> Dict:
        """根据区块号查询区块信息"""
        if isinstance(number, int):
            number = hex(number)
        return self._get_v2_api('proxy', 'eth_getBlockByNumber', {"tag": number, "boolean": boolean})

    # ✅
    def get_uncle_by_block_number_and_index(self, number: str = "latest", index: str = "0x0", boolean: bool = True):
        if isinstance(number, int):
            number = hex(number)
        if isinstance(index, int):
            index = hex(index)
        return self._get_v2_api('proxy', 'eth_getUncleByBlockNumberAndIndex',
                                {"tag": number, "boolean": boolean, "index": index})

    # ✅
    def get_block_tx_count_by_number(self, number: str, boolean: bool = True) -> int:
        if isinstance(number, int):
            number = hex(number)
        result_hex = self._get_v2_api('proxy', 'eth_getBlockTransactionCountByNumber',
                                      {"tag": number, "boolean": boolean})
        return int(result_hex, 16)

    # ✅
    def get_tx_by_hash(self, tx_hash: str) -> Dict:
        """"""
        return self._get_v2_api('proxy', 'eth_getTransactionByHash', {"txhash": tx_hash})

    # ✅
    def get_tx_by_block_number_and_index(self, number: str = "latest", index: str = "0x0") -> Dict:
        """"""
        if isinstance(number, int):
            number = hex(number)
        if isinstance(index, int):
            index = hex(index)
        return self._get_v2_api('proxy', 'eth_getTransactionByBlockNumberAndIndex', {"tag": number, "index": index})

    # ✅
    def get_tx_count(self, address: str, tag: str = "latest") -> Dict:
        """get transactions count by address
        tag: latest, earliest, pending"""
        return self._get_v2_api('proxy', 'eth_getTransactionCount', {"address": address, "tag": tag})

    # ✅
    def get_tx_receipt(self, tx_hash: str) -> dict:
        """合约只读调用"""
        return self._get_v2_api('proxy', 'eth_getTransactionReceipt', {"txhash": tx_hash})

    # todo check
    def send_raw_tx(self, hex: str) -> str:
        """"""
        return self._get_v2_api('proxy', 'eth_sendRawTransaction', {"hex": hex})

    # ✅
    def call(self, to: str, data: str, tag: str = "latest"):
        """合约只读调用"""
        return self._get_v2_api('proxy', 'eth_call', {"to": to, "data": data, "tag": tag})

    # ✅
    def get_code(self, address: str, tag: str = "latest") -> str:
        """"""
        return self._get_v2_api('proxy', 'eth_getCode', {"address": address, "tag": tag})

    # ✅
    def get_storage_at(self, address: str, position: str, tag: str = "latest") -> str:
        """"""
        return self._get_v2_api('proxy', 'eth_getStorageAt', {"address": address, "position": position, "tag": tag})

    # ✅
    def get_gas_price(self) -> str:
        """"""
        return self._get_v2_api('proxy', 'eth_gasPrice')

    # ✅
    def estimate_gas(self, to: str, data: str, value: str, gas_price: str, gas: str) -> int:
        """"""
        if isinstance(value, int):
            value = hex(value)
        if isinstance(gas_price, int):
            gas_price = hex(gas_price)
        if isinstance(gas, int):
            gas = hex(gas)
        result_hex = self._get_v2_api('proxy', 'eth_estimateGas',
                                      {"data": data, "to": to, "value": value,
                                       "gas_price": gas_price, "gas": gas})
        return int(result_hex, 16)
