from tests.conftest import tx_hash


def test_get_block_number(etherscan):
    result = etherscan.get_block_number()
    print(result)


def test_get_block_by_number(etherscan, block_no):
    result = etherscan.get_block_by_number("latest")
    print(result)

    result = etherscan.get_block_by_number(block_no)
    print(result)


def test_get_uncle_by_block_number_and_index(etherscan, block_no):
    result = etherscan.get_uncle_by_block_number_and_index(block_no, 0)
    print(result)



def test_get_block_tx_count_by_number(etherscan, block_no):
    result = etherscan.get_block_tx_count_by_number(block_no)
    print(result)


def test_get_tx_by_hash(etherscan, tx_hash):
    result = etherscan.get_tx_by_hash(tx_hash)
    print(result)

def test_get_tx_by_block_number_and_index(etherscan, block_no):
    result = etherscan.get_tx_by_block_number_and_index(block_no, 1)
    print(result)


def test_get_tx_count(etherscan, account):
    result = etherscan.get_tx_count(account)
    print(result)

def test_eth_call(etherscan):
    pass


def test_get_code(etherscan, usdt):
    result = etherscan.get_code(usdt)
    print(result)

def test_get_storage_at(etherscan, usdt):
    result = etherscan.get_storage_at(usdt, "0x0")
    print(result)

def test_get_gas_price(etherscan):
    result = etherscan.get_gas_price()
    print(result)

def test_estimate_gas(etherscan):
    result = etherscan.estimate_gas(data='0x4e71d92d', to='0xf0160428a8552ac9bb7e050d90eeade4ddd52843', value="0xff22",
                                    gas_price='0x51da038cc', gas='0x5f5e0ff')
    print(result)

def test_get_tx(etherscan, tx_hash):
    result = etherscan.get_tx_receipt(tx_hash)
    print(result)