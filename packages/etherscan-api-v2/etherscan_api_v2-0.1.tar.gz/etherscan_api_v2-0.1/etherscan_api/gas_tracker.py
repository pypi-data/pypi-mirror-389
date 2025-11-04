from etherscan_api.base import BaseApi


class GasTrackerApiMixIn(BaseApi):
    pass


class GasTrackerProApiMixIn(BaseApi):
    # ❌ not found action in free api
    def get_gas_estimate(self, gas_price: str):
        return self._get_v2_api('gastracker', 'gasestimate', {'gasprice': gas_price})

    # ❌ not found action in free api
    def get_gas_oracle(self):
        return self._get_v2_api('gastracker', 'gasoracle')

    # only pro user ❌
    def get_daily_avg_gas_limit(self, start_date: str, end_date: str, sort: str = 'desc'):
        return self._get_v2_api('stats', 'dailyavggaslimit',
                                {'startdate': start_date, 'enddate': end_date, 'sort': sort})

    # only pro user ❌
    def get_daily_gas_used(self, start_date: str, end_date: str, sort: str = 'desc'):
        return self._get_v2_api('stats', 'dailygasused', {'startdate': start_date, 'enddate': end_date, 'sort': sort})

    # only pro user ❌
    def get_daily_avg_gas_price(self, start_date: str, end_date: str, sort: str = 'desc'):
        return self._get_v2_api('stats', 'dailyavggasprice',
                                {'startdate': start_date, 'enddate': end_date, 'sort': sort})
