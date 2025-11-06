import json
from typing import Dict, List, Any

import eth_abi
from ._keccak import Keccak256


from etherscan_api.base import BaseApi, EtherscanApiError


def get_method_sig(method, input_types: List[str]):
    text = f"{method}()" if input_types is None else f"{method}({','.join(input_types)})"
    return f'0x{Keccak256(text.encode()).hexdigest()[:8]}'


def get_call_data(method, input_types: List[str], args):
    assert len(input_types) == len(args), 'length input_types and args should be the same'
    if len(input_types) == 0:
        return get_method_sig(method, [])
    return get_method_sig(method, input_types) + eth_abi.encode(input_types, args).hex()


def _get_input_output_types_from_abi(abi: List[Dict], method):
    assert isinstance(abi, list), 'abi should be list type'
    for item in abi:
        if item.get('name') == method and item.get('type').lower() == "function":
            input_types = [i['type'] for i in item['inputs']]
            output_types = [i['type'] for i in item['outputs']]
            return input_types, output_types
    else:
        raise EtherscanApiError(f'function {method} not found in abi')


class ContractApiMixIn(BaseApi):
    # Contract API ------------------------------------------------------------------
    # ✅
    def get_contract_abi(self, address: str) -> str:
        """Get registered contract abi"""
        return self._get_v2_api('contract', 'getabi', {"address": address})

    # ✅
    def get_contract_source_code(self, address: str) -> List[Dict]:
        """Get registered contract source code"""
        return self._get_v2_api('contract', 'getsourcecode', {"address": address})

    # ✅
    def get_contract_creation(self, contract_addresses: str) -> List[Dict]:
        """Get registered contract creator and creation tx hash
        eg. [{'contractAddress': '0x58c885900f2df7a1fb1cc1ec35dea9a1c786cac0',
           'contractCreator': '0xfd740f0f180cb293710b0d90b9e969cad9c9e2b0',
           'txHash': '0x4812f2faa6d56c45f6527c21641daeef36b0086c8b0b77316787dc0fcca212de',
           'blockNumber': '8822474', 'timestamp': '1753244160', 'contractFactory': '',
           'creationBytecode': '0x608060405260008...'}]
        """

        return self._get_v2_api('contract', 'getcontractcreation', {"contractaddresses": contract_addresses})

    def check_verify_status(self, address: str, guid: str) -> List[Dict]:
        """"""
        return self._get_v2_api('contract', 'checkverifystatus', {"address": address, "guid": guid})

    def check_proxy_verification(self, address: str, guid: str) -> List[Dict]:
        """"""
        return self._get_v2_api('contract', 'checkproxyverification', {"address": address, "guid": guid})

    def verify_source_code(self, contract_address: str, source_code: str,
                           contract_name: str,
                           constructor_arguments: str,
                           code_format: str = "solidity-standard-json-input",
                           compiler_version: str = "v0.8.24+commit.e11b9ed9",
                           optimization_used: str = 0, runs: str = 200,
                           evm_version="default",
                           license_type: str = 1,
                           zksolc_version: str = "1.2.13",
                           compiler_mode: str = None
                           ):
        params = {"contractaddress": contract_address, "sourceCode": source_code, "codeformat": code_format,
                  "contractname": contract_name, 'constructorArguments': constructor_arguments}
        if code_format == "vyper-json":
            compiler_version = compiler_version or "vyper:0.4.0"
            return self._post_v2_api('contract', 'verifysourcecode',
                                     {**params, 'compilerversion': compiler_version,
                                      'optimizationUsed': optimization_used,
                                      })
        if code_format == "stylus":
            compiler_version = compiler_version or "stylus:0.5.3"
            return self._post_v2_api('contract', 'verifysourcecode',
                                     {**params, 'compilerversion': compiler_version,
                                      'optimizationUsed': optimization_used,
                                      'licenseType': license_type})

        compiler_version = compiler_version or "v0.8.24+commit.e11b9ed9"
        if compiler_mode == 'zksync':
            return self._post_v2_api('contract', 'verifysourcecode',
                                     {**params, 'compilerversion': compiler_version,
                                      'zksolcVersion': zksolc_version, 'comilermode': compiler_mode})

        return self._post_v2_api('contract', 'verifysourcecode',
                                 {**params, 'compilerversion': compiler_version, 'optimizationUsed': optimization_used,
                                  'runs': runs,
                                  'evmVersion': evm_version, 'licenseType': license_type})

    # ✅
    def _query_contract(self, contract_address: str, method: str, *args, input_types: list = (),
                        output_types: list = None) -> Any:
        """Query contract with input_types and output_types"""
        data = get_call_data(method, input_types, args)
        _result = self.call(to=contract_address, data=data)
        if output_types is None:
            return _result
        result = eth_abi.decode(output_types, bytes.fromhex(_result[2:]))
        if len(result) == 1:
            return result[0]

    # ✅
    def query_contract(self, contract_address: str, method: str, *args, abi: List[Dict] = None) -> Any:
        """Query contract with abi"""
        abi = abi or json.loads(self.get_contract_abi(contract_address))
        if not isinstance(abi, list):
            raise EtherscanApiError("abi should be type of list")
        input_types, output_types = _get_input_output_types_from_abi(abi, method)
        return self._query_contract(contract_address, method, *args, input_types=input_types, output_types=output_types)
