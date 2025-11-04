from etherscan_api.base import BaseApi


class StatsApiMixIn(BaseApi):
    # ✅
    def get_eth_supply(self) -> str:
        """ETH 总供应量"""
        return self._get_v2_api('stats', 'ethsupply')

    # ✅
    def get_eth_price(self) -> str:
        """ETH 最新价格"""
        return self._get_v2_api('stats', 'ethprice')


class StatsProApiMixIn(BaseApi):
    # ❌ not found action in free api
    def get_eth_supply2(self) -> str:
        """ETH 总供应量"""
        return self._get_v2_api('stats', 'ethsupply2')

    # ❌ not found action in free api
    def get_chain_size(self, start_date: str, end_date: str, client_type: str = "geth", sync_mode: str = "default",
                       sort: str = "desc") -> str:
        """节点大小"""
        return self._get_v2_api('stats', 'chainsize',
                                params={'startdate': start_date, 'enddate': end_date, 'clienttype': client_type,
                                        'syncmode': sync_mode, 'sort': sort})

    # ❌ not found action in free api
    def get_node_count(self) -> str:
        """节点数量"""
        return self._get_v2_api('stats', 'nodecount')

    # ❌ only for pro user
    def get_daily_tx_fee(self, start_date: str, end_date: str, sort: str = 'desc') -> str:
        """"""
        return self._get_v2_api('stats', 'dailytxnfee',
                                {'startdate': start_date, 'enddate': end_date, 'sort': sort})

    # ❌ only for pro user
    def get_daily_new_address_count(self, start_date: str, end_date: str, sort: str = 'desc') -> str:
        """"""
        return self._get_v2_api('stats', 'dailynewaddress',
                                {'startdate': start_date, 'enddate': end_date, 'sort': sort})

    # ❌ only for pro user
    def get_daily_net_utilization(self, start_date: str, end_date: str, sort: str = 'desc') -> str:
        """"""
        return self._get_v2_api('stats', 'dailynetutilization',
                                {'startdate': start_date, 'enddate': end_date, 'sort': sort})

    # ❌ only for pro user
    def get_daily_avg_hashrate(self, start_date: str, end_date: str, sort: str = 'desc') -> str:
        """"""
        return self._get_v2_api('stats', 'dailyavghashrate',
                                {'startdate': start_date, 'enddate': end_date, 'sort': sort})

    # ❌ only for pro user
    def get_daily_tx_count(self, start_date: str, end_date: str, sort: str = 'desc') -> str:
        """"""
        return self._get_v2_api('stats', 'dailytx',
                                {'startdate': start_date, 'enddate': end_date, 'sort': sort})

    # ❌ only for pro user
    def get_daily_avg_net_difficulty(self, start_date: str, end_date: str, sort: str = 'desc') -> str:
        """"""
        return self._get_v2_api('stats', 'dailyavgnetdifficulty',
                                {'startdate': start_date, 'enddate': end_date, 'sort': sort})

    # ❌ only for pro user
    def get_daily_price(self, start_date: str, end_date: str, sort: str = 'desc') -> str:
        """"""
        return self._get_v2_api('stats', 'ethdailyprice',
                                {'startdate': start_date, 'enddate': end_date, 'sort': sort})
