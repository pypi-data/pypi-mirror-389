from pprint import pprint

from etherscan_api import get_etherscan_api
from etherscan_api.etherscan_api import EtherScanApi


def test_chain_list(etherscan):
    result = EtherScanApi.chain_list()
    d = {}
    for i in result:
        key = i['chainname'].replace(" ", "_").lower()
        d[key] = i['chainid']
    pprint(d)


def test_bsc_suddd_valid_holders():
    bsc = get_etherscan_api('bsc', network='testnet')
    bsc_susdd = '0x3b0804c4de1dc18b285c0035ff0bf54d84cf5bd7'
    valid_holders = bsc.get_token_valid_holders(bsc_susdd)
    print(len(valid_holders))
