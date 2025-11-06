from eth_hash.auto import keccak


def test_get_token_supply(etherscan, usdt):
    result = etherscan.get_token_supply(usdt)
    print(result)


def test_get_token_balance(etherscan, usdt, account):
    result = etherscan.get_token_balance(usdt, account)
    print(result)


def test_get_token_holders(etherscan, usdt):
    holders = etherscan.get_token_holders(usdt)
    print(len(holders))


def test_get_token_valid_holders(etherscan, usdt):
    holders = etherscan.get_token_valid_holders(usdt)
    print(len(holders))


def test_get_token_top_holders(etherscan, usdt):
    holders = etherscan.get_token_top_holders(usdt)
    print(len(holders))


def test_get_token_holders_and_balance(etherscan, usdt):
    valid_holders = etherscan.get_token_valid_holders(usdt)
    print(len(valid_holders))