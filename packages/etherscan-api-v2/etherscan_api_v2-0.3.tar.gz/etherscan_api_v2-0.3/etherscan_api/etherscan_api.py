import requests

from etherscan_api.account import AccountMixInApi, AccountProApiMixIn
from etherscan_api.base import EtherscanApiError
from etherscan_api.block import BlockApiMixIn, BlockProApiMixIn
from etherscan_api.contract import ContractApiMixIn
from etherscan_api.gas_tracker import GasTrackerApiMixIn, GasTrackerProApiMixIn
from etherscan_api.layer2 import Layer2ApiMixIn
from etherscan_api.logs import LogsApiMixIn
from etherscan_api.proxy import ProxyApiMixIn
from etherscan_api.stats import StatsApiMixIn, StatsProApiMixIn
from etherscan_api.token import TokenApiMixIn, TokenProApiMixIn, TokenExtraApiMixIn
from etherscan_api.transaction import TransactionApiMixIn

ETHERSCAN_BASE_URL = 'https://api.etherscan.io'

CHAIN_IDS = {
    'abstract_mainnet': '2741',
    'abstract_sepolia_testnet': '11124',
    'apechain_curtis_testnet': '33111',
    'apechain_mainnet': '33139',
    'arbitrum_nova_mainnet': '42170',
    'arbitrum_one_mainnet': '42161',
    'arbitrum_sepolia_testnet': '421614',
    'avalanche_c-chain': '43114',
    'avalanche_fuji_testnet': '43113',
    'base_mainnet': '8453',
    'base_sepolia_testnet': '84532',
    'berachain_bepolia_testnet': '80069',
    'berachain_mainnet': '80094',
    'bittorrent_chain_mainnet': '199',
    'bittorrent_chain_testnet': '1029',
    'blast_mainnet': '81457',
    'blast_sepolia_testnet': '168587773',
    'bnb_smart_chain_mainnet': '56',
    'bnb_smart_chain_testnet': '97',
    'celo_mainnet': '42220',
    'celo_sepolia_testnet': '11142220',
    'ethereum_mainnet': '1',
    'fraxtal_hoodi_testnet': '2523',
    'fraxtal_mainnet': '252',
    'gnosis': '100',
    'holesky_testnet': '17000',
    'hoodi_testnet': '560048',
    'hyperevm_mainnet': '999',
    'katana_bokuto': '737373',
    'katana_mainnet': '747474',
    'linea_mainnet': '59144',
    'linea_sepolia_testnet': '59141',
    'mantle_mainnet': '5000',
    'mantle_sepolia_testnet': '5003',
    'memecore_testnet': '43521',
    'monad_testnet': '10143',
    'moonbase_alpha_testnet': '1287',
    'moonbeam_mainnet': '1284',
    'moonriver_mainnet': '1285',
    'op_mainnet': '10',
    'op_sepolia_testnet': '11155420',
    'opbnb_mainnet': '204',
    'opbnb_testnet': '5611',
    'polygon_amoy_testnet': '80002',
    'polygon_mainnet': '137',
    'scroll_mainnet': '534352',
    'scroll_sepolia_testnet': '534351',
    'sei_mainnet': '1329',
    'sei_testnet': '1328',
    'sepolia_testnet': '11155111',
    'sonic_mainnet': '146',
    'sonic_testnet': '14601',
    'sophon_mainnet': '50104',
    'sophon_sepolia_testnet': '531050104',
    'swellchain_mainnet': '1923',
    'swellchain_testnet': '1924',
    'taiko_hoodi': '167013',
    'taiko_mainnet': '167000',
    'unichain_mainnet': '130',
    'unichain_sepolia_testnet': '1301',
    'world_mainnet': '480',
    'world_sepolia_testnet': '4801',
    'xdc_apothem_testnet': '51',
    'xdc_mainnet': '50',
    'zksync_mainnet': '324',
    'zksync_sepolia_testnet': '300',
    # extra
    'bsc_mainnet': '56',
    'bsc_testnet': '97',
    'plasma_mainnet': '9745',
    'plasma_testnet': '9746',

}


class EtherScanApi(AccountMixInApi, TokenApiMixIn, BlockApiMixIn, TransactionApiMixIn, LogsApiMixIn,
                   ContractApiMixIn, ProxyApiMixIn, StatsApiMixIn, Layer2ApiMixIn, GasTrackerApiMixIn,
                   TokenExtraApiMixIn):
    """
    doc：https://docs.etherscan.io/apis
    """

    @staticmethod
    def chain_list():
        return requests.get(ETHERSCAN_BASE_URL + '/v2/chainlist').json()['result']


class EtherScanProApi(EtherScanApi, AccountProApiMixIn, BlockProApiMixIn, GasTrackerProApiMixIn, StatsProApiMixIn,
                      TokenProApiMixIn):
    # ❌ pro api
    def get_address_tag(self, address: str):
        return self._get_v2_api('nametag', 'getaddresstag', {'address': address})


def get_etherscan_api(chain='eth', network='mainnet', api_key=None):
    if chain == 'eth':
        chain = 'ethereum'
    key1, key2, key3 = f'{chain}_{network}', f'{chain}_sepolia_{network}', f'sepolia_{network}'

    chain_id = CHAIN_IDS.get(key1) or CHAIN_IDS.get(key2) or CHAIN_IDS.get(key3)
    if chain_id is None:
        raise EtherscanApiError(f'{chain}_{network} chain id not found')
    return EtherScanApi(chain_id=chain_id, api_key=api_key)
