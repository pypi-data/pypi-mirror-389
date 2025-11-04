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





def test_demo():
    # from eth_utils import keccak
    # r = keccak(text='balanceOf()')
    # print(r)
    from sha3 import keccak_256
    from .keccak import Keccak256

    k = keccak_256(b'balanceOf()')

    r = k.hexdigest()
    print(r)

    r2 = Keccak256(b'balanceOf()').hexdigest()
    print(r2)
