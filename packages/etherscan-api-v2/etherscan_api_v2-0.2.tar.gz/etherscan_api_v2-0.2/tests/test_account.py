from pprint import pprint


def test_get_balance(etherscan, account):
    result = etherscan.get_balance(account)
    print(result)


def test_get_balances(etherscan, account):
    result = etherscan.get_balances([account])
    print(result)


def test_get_token_balance(etherscan, account, usdt):
    result = etherscan.get_token_balance(account, contract_address=usdt)
    print(result)


def test_get_tx_list(etherscan, account):
    result = etherscan.get_tx_list(account)
    print(len(result))


def test_get_internal_tx_list(etherscan, account, tx_hash):
    result = etherscan.get_internal_tx_list(account)
    print(len(result))

    result = etherscan.get_internal_tx_list()
    print(len(result))

    result = etherscan.get_internal_tx_list(tx_hash=tx_hash)
    print(len(result))



def test_get_token_tx_list(etherscan, usdt):
    result = etherscan.get_token_tx_list(contract_address=usdt)
    pprint(result)


def test_get_token_nft_tx_list(etherscan, account):
    result = etherscan.get_token_nft_tx_list(account)
    print(len(result))


def test_get_token_1155_tx_list(etherscan, account):
    result = etherscan.get_token_1155_tx_list(account)
    print(len(result))


def test_get_mined_blocks(etherscan, account):
    result = etherscan.get_mined_blocks(account)
    print(len(result))
