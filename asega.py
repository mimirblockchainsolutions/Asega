"""Asega.

Usage: asega.py ( --contract FILENAME ) ( --test PATH ) [ --host IPADDR ] [ --port PORT ] [ --account ADDR ] [ --pass PASS ]


-h --help                   Show this screen.
-v --version                Print the program version.
--contract FILENAME         Path to contract to be tested.
--test PATH                 Path to test specifications directory.
--host IPADDR               IP address or dns name of Ethereum Client.[default: 127.0.0.1]
--port PORT                 Port of Ethereum Client.[default: 8545]
--account ADDR              Address of the account to use.[default: 0x00a329c0648769a73afac7f9381e08fb43dbea72]
--pass PASS                 Password of the account to use[default: None]
"""

if __name__ == "__main__":
    import web3
    from web3 import Web3,HTTPProvider
    from solc import compile_files,compile_source
    import itertools
    import time
    import docopt


    class Caller(object):
        __slots__ = ["host","port","passphrase","w3","account"]
        def __init__(self,host,port,passphrase,account):
            self.w3 = Web3(HTTPProvider("http://{}:{}".format(host,port)))
            # set pre-funded account as sender
            account = Web3.toChecksumAddress(account)
            self.w3.eth.defaultAccount = account
            self.passphrase = passphrase
            self.account = account

        def unlock(self):
            self.w3.personal.unlockAccount(self.account,self.passphrase)

    class Dev(object):
        __slots__ = ["name","address","target_name","caller","target_contract_call","target_contract_transaction"]
        def __init__(self, name, target_name, caller):
            self.caller = caller
            self.name = name
            self.target_name = target_name
            self.address = None
            self.target_contract_call = None
            self.target_contract_transaction = None

        def set_target(self,address,abi):
            ct_out = self.caller.w3.eth.contract(
                address=address,
                abi=abi,
            )
            cc_out = self.caller.w3.eth.contract(
                address=address,
                abi=abi,
            )
            self.target_contract_transaction=ct_out
            self.target_contract_call=cc_out
            self.address = self.caller.w3.toChecksumAddress("0x00a329c0648769a73afac7f9381e08fb43dbea72")
            return self


    class Ident(object):
        __slots__ = ["name","address","target_name","contract","caller","target_contract_call","target_contract_transaction"]
        def __init__(self, name, target_name, caller):
            self.caller = caller
            self.name = name
            self.target_name = target_name
            self.address = None
            self.contract = None
            self.target_contract_call = None
            self.target_contract_transaction = None
            self.deploy_test_ident()

        def set_target(self,address,abi):
            self.caller.unlock()
            thash = self.contract.functions.set_target(address).transact()
            receipt = self.caller.w3.eth.waitForTransactionReceipt(thash)
            ct_out = self.caller.w3.eth.contract(
                address=self.address,
                abi=abi,
            )
            cc_out = self.caller.w3.eth.contract(
                address=address,
                abi=abi,
            )
            self.target_contract_transaction=ct_out
            self.target_contract_call=cc_out
            return self

        def compile_test_ident(self):
            source_code = '''
                pragma solidity ^0.4.24;

                contract TestIdentity{

                  address target;

                  constructor()
                  public{
                  }

                  function set_target(address _target)
                  public {
                    target = _target;
                  }

                  function()
                  public
                  payable {
                    require(target.call.value(msg.value)(msg.data));
                  }

                }'''

            compiled_sol = compile_source(source_code)
            contract_interface = compiled_sol['<stdin>:TestIdentity']
            abi = contract_interface["abi"]
            bytecode = contract_interface["bin"]
            return abi,bytecode

        def deploy_test_ident(self):
            abi,bytecode = self.compile_test_ident()
            contract = self.caller.w3.eth.contract(abi=abi, bytecode=bytecode)
            self.caller.unlock()
            tx_hash = contract.constructor().transact()
            tx_receipt = self.caller.w3.eth.waitForTransactionReceipt(tx_hash)
            c_out = self.caller.w3.eth.contract(
                address=tx_receipt.contractAddress,
                abi=abi,
            )
            self.contract = c_out
            self.address = tx_receipt.contractAddress

    def run(caller, ident_spec_file, contract_filename, contract_spec_file,test_spec_file):
        start_time = time.time()
        print("BUILDING IDENTS")
        idents = build_idents(caller,ident_spec_file)
        contracts = build_contracts(caller, contract_filename, contract_spec_file, idents)
        idents = link_ident_targets(idents,contracts)
        print("PARSING TESTS")
        tests = build_tests(test_spec_file,idents)
        run_tests(idents,tests,start_time)

    def build_idents(caller,ident_spec_file):
        lines = read_file(ident_spec_file)
        idents = {}
        for line in lines:
            line = line.split(':')
            if line[0] != 'dev':
                idents[line[0]] = Ident(line[0],line[1],caller)
            else:
                idents[line[0]] = Dev(line[0],line[1],caller)
        return idents

    def compile_contracts(filename):
        with open(filename,'r') as f:
            contract_source_code = f.read()
        return compile_files([filename])

    def build_contracts(caller, contract_filename, contract_spec_file, idents):
        compiled_sol = compile_contracts(contract_filename)
        contract_spec_lines = read_file(contract_spec_file)
        contracts = {}
        for line in contract_spec_lines:
            line = line.split(':')
            contract_name = line[0]
            contract_interface = compiled_sol['{}:{}'.format(contract_filename,contract_name)]
            contract = caller.w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
            arg_list = line[1]
            #strip list brackets
            arg_list = arg_list[1:-1]
            args = arg_list.split(',')
            arg_list = []
            for arg in args:
                arg_list.append(parse_constructor_arg(arg,idents))
            constructor = [item for item in contract_interface["abi"] if item["type"] == 'constructor'][0]
            argtypes = [arg["type"] for arg in constructor["inputs"]]
            addresses = [argtype == 'address' for argtype in argtypes]
            uint256es = [argtype == 'uint256' for argtype in argtypes]
            arglist = [caller.w3.toChecksumAddress(arg) if addresses[i] else arg for i,arg in enumerate(arg_list)]
            arglist = [int(arg) if uint256es[i] else arg for i,arg in enumerate(arglist)]
            caller.unlock()
            # Submit the transaction that deploys the contract
            tx_hash = contract.constructor(*arglist).transact()
            # Wait for the transaction to be mined, and get the transaction receipt
            tx_receipt = caller.w3.eth.waitForTransactionReceipt(tx_hash)
            contract = caller.w3.eth.contract(address=tx_receipt.contractAddress,abi=contract_interface["abi"])
            contracts[line[0]] = contract
        return contracts

    def parse_constructor_arg(arg,idents):
        if arg[0] == '$':
            ident = arg[1:].replace(']','')
            return idents[ident].address
        else:
            return arg

    def link_ident_targets(idents, contracts):
        idents_out = {}
        for ident in idents:
            abi = contracts[idents[ident].target_name].abi
            address = contracts[idents[ident].target_name].address
            idents_out[ident] = idents[ident].set_target(address,abi)
        return idents_out

    def read_file(filename):
        with open(filename) as f:
            lines = f.readlines()
        lines = [line.replace('\n','') for line in lines]
        lines = [line.replace(' ','') for line in lines]
        return lines

    def determine_test_line_type(lines):
        line_types = []
        for line in lines:
            if len(line) > 0:
                if len(line) == 1:
                    if line[0] != '#':
                        raise Exception
                    else:
                        continue
                elif len(line) >= 2:
                    if line[0] == '#':
                        line_types.append(False)
                    else:
                        line_types.append(True)
                else:
                    Exception #IMPOSSIBLE!
            elif len(line) == 0:
                line_types.append(False)
            else:
                Exception #IMPOSSIBLE!
        return line_types

    def get_test_lines(lines,line_types):
        assert len(lines) == len(line_types), "Length mismatch"
        return [lines[i] for i, check in enumerate(line_types) if check]

    def build_tests(test_filename,idents):
        lines = read_file(test_filename)
        line_types = determine_test_line_type(lines)
        tests_lines = get_test_lines(lines,line_types)
        return parse_tests(tests_lines,idents)

    def parse_tests(lines,idents):
        tests = []
        for line in lines:
            test = line.split(':')
            operation = parse_operation(test[0])
            ident_list = parse_idents(test[1],idents)
            method = test[2]
            args_list = parse_args(test[3],idents)
            result = parse_result(operation, test[4])
            tests.append([operation,ident_list,method,args_list,result])
        return tests

    def set_state(idents,ident,method,args,result):
        call = getattr(idents[ident].target_contract_transaction.functions,method)
        args = list(args)
        abis = idents[ident].target_contract_transaction.abi
        function_abis = [abi for abi in abis if abi["type"]=="function"]
        function_abi = [abi for abi in function_abis if abi["name"]==method][0]
        inputs = [ins["type"] for ins in function_abi["inputs"]]
        if len(inputs) > 0:
            for i,arg in enumerate(args):
                if inputs[i] == 'uint256' or inputs[i] == 'uint8':
                    args[i] = int(args[i])
                if inputs[i] == 'address':
                    args[i] = Web3.toChecksumAddress(args[i])
        else:
            args = []
        try:
            idents[ident].caller.unlock()
            thash = call(*args).transact()
            receipt = idents[ident].caller.w3.eth.waitForTransactionReceipt(thash)
        except Exception as e:
            if result == True:
                outcome = str(e)
            else:
                outcome = False
        else:
            outcome = True
        return [outcome,result]

    def check_state(idents,ident,method,args,result):
        call = getattr(idents[ident].target_contract_call.functions,method)
        args = list(args)
        abis = idents[ident].target_contract_transaction.abi
        function_abis = [abi for abi in abis if abi["type"]=="function"]
        function_abi = [abi for abi in function_abis if abi["name"]==method][0]
        inputs = [ins["type"] for ins in function_abi["inputs"]]
        if len(inputs) > 0:
            for i,arg in enumerate(args):
                if inputs[i] == 'uint256' or inputs[i] == 'uint8':
                    args[i] = int(args[i])
                if inputs[i] == 'address':
                    args[i] = Web3.toChecksumAddress(args[i])
        else:
            args = []
        outcome = call(*args).call()
        if type(outcome) == int:
            result = int(result)
        return [outcome,result]

    def parse_operation(operation):
        if operation == "set":
            return set_state
        elif operation == "assert":
            return check_state
        else:
            raise Exception

    def parse_idents(ident, idents):
        if ident[0] == '$':
            if ident[1] == '!':
                return [idt for idt in idents if ident[2:] != idents[idt].name]
            if ident[1] == '*':
                return [idt for idt in idents]
            else:
                raise Exception
        else:
            return [ident]

    def parse_args(args,idents):
        arg_list = args.split(',')
        return [parse_arg(arg,idents) for arg in arg_list]

    def parse_arg(arg, idents):
        if len(arg) == 0: return [None]
        if arg[0] == '$':
            if arg[1] == '!':
                return [idents[idt].address for idt in idents if idents[idt].name != arg[2:]]
            elif arg[1] == '*':
                return [idents[idt].address for idt in idents]
            else:
                return [idents[arg[1:]].address]
        else:
            return [arg]

    def parse_result(operation, result):
        if operation == set_state:
            if result == "True":
                result = True
            elif result == "False":
                result = False
            else:
                raise Exception
        elif operation == check_state:
            if result == "True":
                result = True
            elif result == "False":
                result = False
            else:
                pass
        else:
            raise Exception
        return result

    def run_test(idents,operation,test_idents,method,args,result):
        arg_permutations = list(itertools.product(*args))
        results = []
        for ident in test_idents:
            for arg_permutation in arg_permutations:
                out = operation(idents,ident,method,arg_permutation,result)
                if type(out[0]) == str:
                    out[0] = out[0].lower()
                if type(out[1]) == str:
                    out[1] = out[1].lower()
                if out[0] == out[1]:
                    results.append(True)
                else:
                    print('--------------------------------------------------')
                    print("FAILURE")
                    print("    EXPECTED:",out[1])
                    print("    RESULT WAS:",out[0])
                    print('   ',operation.__name__,ident,method,arg_permutation,result)
                    results.append(False)
        return results

    def run_tests(idents,tests,start_time):
        print('RUNNING TESTS')
        pass_count = 0
        fail_count = 0
        line_count = 0
        for test in tests:
            line_count += 1
            results = run_test(idents,test[0],test[1],test[2],test[3],test[4])
            for result in results:
                if result:
                    pass_count+=1
                else:
                    fail_count+=1
                    print("    OCCURED IN TEST(S) ON LINE",line_count)
        stop_time = time.time()
        print('----------------------------------------------------')
        if fail_count == 0:
            print('-----------------ALL TESTS PASSED-------------------')
        else:
            print('----------------------FAILURE-----------------------')
        print('----------------------------------------------------')
        print("SUMMARY:")
        print("    RAN {} TEST(S) IN {} SECONDS".format(fail_count+pass_count,stop_time-start_time))
        print("        {} TEST(S) PASSED".format(pass_count))
        print("        {} TEST(S) FAILED".format(fail_count))


    #parses the cli input options
    kwargs = docopt.docopt(__doc__,version='0.0.1')
    if kwargs["--pass"] == "None":
        kwargs["--pass"] = ""
    caller = Caller(kwargs["--host"],kwargs["--port"],kwargs["--pass"],kwargs["--account"])
    ident_spec_file = kwargs["--test"] + "ident.spec"
    test_spec_file = kwargs["--test"] +"test.spec"
    contract_spec_file = kwargs["--test"] +"contract.spec"
    contract_filename = "./contracts/"+kwargs["--contract"]
    run(caller, ident_spec_file, contract_filename, contract_spec_file,test_spec_file)
