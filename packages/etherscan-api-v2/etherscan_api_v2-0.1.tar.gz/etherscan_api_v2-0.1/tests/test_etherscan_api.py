from pprint import pprint

from etherscan_api.etherscan_api import EtherScanApi


def test_chain_list(etherscan):
    result = EtherScanApi.chain_list()
    d = {}
    for i in result:
        key = i['chainname'].replace(" ", "_").lower()
        d[key] = i['chainid']
    pprint(d)
