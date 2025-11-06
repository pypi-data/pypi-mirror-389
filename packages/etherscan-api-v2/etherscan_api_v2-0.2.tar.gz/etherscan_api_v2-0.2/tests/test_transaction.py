def test_get_tx_status(etherscan, tx_hash):
    result = etherscan.get_tx_status(tx_hash)
    print(result)


def test_get_tx_receipt_status(etherscan, tx_hash):
    result = etherscan.get_tx_receipt_status(tx_hash)
    print(result)