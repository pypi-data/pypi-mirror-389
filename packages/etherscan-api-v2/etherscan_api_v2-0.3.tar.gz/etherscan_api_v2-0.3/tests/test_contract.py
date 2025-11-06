import json
from pprint import pprint


def test_get_contract_abi(etherscan, usdt):
    result = etherscan.get_contract_abi(usdt)
    pprint(json.loads(result))  # str


def test_get_contract_source_code(etherscan, usdt):
    result = etherscan.get_contract_source_code(usdt)
    print(result)  # str


def test_get_contract_creation(etherscan, usdt):
    result = etherscan.get_contract_creation(usdt)
    print(result)


def test_query_contract(etherscan, usdt, account):
    result = etherscan._query_contract(usdt, 'balanceOf', account, input_types=('address',), output_types=('uint256',))
    print(result)

    abi = [{
        "outputs": [{"type": "uint256"}],
        "constant": True,
        "inputs": [{"name": "who", "type": "address"}],
        "name": "balanceOf",
        "stateMutability": "view",
        "type": "function"
    }]
    result = etherscan.query_contract(usdt, 'balanceOf', account, abi=abi)
    print(result)

    result = etherscan.query_contract(usdt, 'balanceOf', account)
    print(result)
