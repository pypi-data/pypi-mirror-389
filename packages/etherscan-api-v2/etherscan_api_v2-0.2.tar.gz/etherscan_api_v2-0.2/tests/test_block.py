

def test_get_block_reward(etherscan, block_no):
    result = etherscan.get_block_reward(block_no)
    print(result)


def test_get_block_countdown(etherscan):
    latest_block_no = etherscan.get_block_number()
    result = etherscan.get_block_countdown(latest_block_no)
    print(result)


def test_get_block_no_by_time(etherscan, block_timestamp, block_no):
    result = etherscan.get_block_no_by_time(block_timestamp)
    print(result)
    assert result == block_no
