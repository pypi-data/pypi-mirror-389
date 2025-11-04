from typing import Dict

from etherscan_api.base import BaseApi


class BlockApiMixIn(BaseApi):
    # ✅
    def get_block_reward(self, block_no: int) -> Dict:
        return self._get_v2_api('block', 'getblockreward', {"blockno": block_no})

    # ✅
    def get_block_countdown(self, block_no: int) -> Dict:
        """"""
        return self._get_v2_api('block', 'getblockcountdown', {"blockno": block_no})

    # ✅
    def get_block_no_by_time(self, timestamp: int, closest: str = "before") -> int:
        """"""
        block_no = self._get_v2_api('block', 'getblocknobytime', {"timestamp": timestamp, "closest": closest})
        return int(block_no)

class BlockProApiMixIn(BaseApi):
    # only pro user ❌
    def get_daily_avg_block_size(self, start_date: str, end_date: str, sort: str = 'desc') -> Dict:
        """"""
        return self._get_v2_api('stats', 'dailyavgblocksize',
                                {"startdate": start_date, 'enddate': end_date, 'sort': sort})

    # only pro user ❌
    def get_daily_block_count(self, start_date: str, end_date: str, sort: str = 'desc') -> Dict:
        """"""
        return self._get_v2_api('stats', 'dailyblkcount',
                                {"startdate": start_date, 'enddate': end_date, 'sort': sort})

    # only pro user ❌
    def get_daily_block_rewards(self, start_date: str, end_date: str, sort: str = 'desc') -> Dict:
        """"""
        return self._get_v2_api('stats', 'dailyblockrewards',
                                {"startdate": start_date, 'enddate': end_date, 'sort': sort})

    # only pro user ❌
    def get_daily_avg_block_time(self, start_date: str, end_date: str, sort: str = 'desc') -> Dict:
        """"""
        return self._get_v2_api('stats', 'dailyavgblocktime',
                                {"startdate": start_date, 'enddate': end_date, 'sort': sort})

    # only pro user ❌
    def get_daily_uncle_block_count(self, start_date: str, end_date: str, sort: str = 'desc') -> Dict:
        """"""
        return self._get_v2_api('stats', 'dailyuncleblkcount',
                                {"startdate": start_date, 'enddate': end_date, 'sort': sort})
