from etherscan_api.etherscan_api import EtherScanApi


def test_get_plasma_deposits():
    plasma = EtherScanApi(chain_id=137)
    result = plasma.get_plasma_deposits('0x4880bd4695a8e59dc527d124085749744b6c988e')
    print(result)

def test_get_deposit_txs():
    client = EtherScanApi(chain_id=10)
    result = client.get_deposit_txs('0x80f3950a4d371c43360f292a4170624abd9eed03')
    print(result)

def test_get_withdraw_txs():
    client = EtherScanApi(chain_id=10)
    result = client.get_withdraw_txs('0x80f3950a4d371c43360f292a4170624abd9eed03')
    print(result)


