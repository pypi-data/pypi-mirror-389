from etherscan_api.base import BaseApi


class TransactionApiMixIn(BaseApi):
    # ✅
    def get_tx_status(self, tx_hash: str) -> dict:
        """交易回执状态"""
        return self._get_v2_api('transaction', 'getstatus', {"txhash": tx_hash})

    # ✅
    def get_tx_receipt_status(self, tx_hash: str) -> dict:
        """交易回执状态"""
        return self._get_v2_api('transaction', 'gettxreceiptstatus', {"txhash": tx_hash})
