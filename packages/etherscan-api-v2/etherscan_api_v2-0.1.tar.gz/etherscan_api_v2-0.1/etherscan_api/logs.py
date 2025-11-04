from typing import Optional, Dict, List

from etherscan_api.base import BaseApi


class LogsApiMixIn(BaseApi):
    def get_logs(self, from_block: int, to_block: int, address: Optional[str] = None, topic0: Optional[str] = None,
                 topic1: Optional[str] = None, topic2: Optional[str] = None, topic3: Optional[str] = None) -> List[Dict]:
        """get contract event logs by from-to block or topic"""
        params = {"module": "logs", "action": "getLogs", "fromBlock": from_block, "toBlock": to_block}
        if address:
            params["address"] = address
        if topic0:
            params["topic0"] = topic0
        if topic1:
            params["topic1"] = topic1
        if topic2:
            params["topic2"] = topic2
        if topic3:
            params["topic3"] = topic3
        return self._get_v2_api('logs', 'getLogs', params)
