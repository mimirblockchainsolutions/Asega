# Asega Testing Framework

## What

This is the beginning of a testing framework for Ethereum Smart Contracts. It has
been built using Python and is based on the idea of writing easily read tests
in the form of a compact scripting language. The framework has been set up to
handle the creation of multiple identities that can issue commands to the
contract being tested. The following shows how easy it is to test an ERC20
contract:

```
#TEST TRANSFERS OF TOKENS
    assert:None:totalSupply::100
    assert:None:balanceOf:$owner:100
    set:owner:transfer:$token1,100:True
    set:$!token1:transfer:$token1,1:False
    set:token1:transfer:$!token1,1:True
    assert:None:balanceOf:$!token1:1
    set:$!token1:transfer:$token1,1:True
    assert:None:balanceOf:$!token1:0
    assert:None:balanceOf:$token1:100
    set:$!token1:transfer:$token1,1000:False
    assert:None:balanceOf:$!token1:0
    assert:None:balanceOf:$token1:100
    assert:None:totalSupply::100
```

## The Name
Asega:
An asega (legal interpreter or law-speaker) was, in the Middle Ages, an official legal advisor to the court of law in the Westerlauwers district (i.e. west of the River Lauwers) in western Friesland. Unlike a modern judge, the asega gave in most cases only an expert opinion on the law itself rather than on the facts of the case.

[Asega](https://en.wikipedia.org/w/index.php?title=Asega&oldid=834244978)


## Setup

This testing framework has been built using Python3.6
If you do not have python3.6 installed, please visit the Python official docs for
installation instructions.

In order to run this framework you must first install all dependencies using:

`python3.6 -m pip install requirements.txt`

The solidity compiler must also be installed. For the latest directions see:

https://solidity.readthedocs.io/en/latest/installing-solidity.html#binary-packages

Once the dependencies have been installed you must also have an installed
Parity client. This may be installed using the command:

`bash <(curl https://get.parity.io -L)`

Once parity has been installed, Parity must be run using the command:

`parity --chain dev --jsonrpc-apis=all`

This will turn on a private test blockchain on the local machine that the
smart contracts may be deployed and tested against.
The other files that are part of the Asega testing framework are
- `ident.spec` specifies test psuedo-identities using targeted proxies
- `contracts.spec` specifies contracts to be deployed and constructor args
- `test.spec` specifies the actual tests in a scripting language

For details about the scripting language see the comments in `test.spec`
under tests/examples
In order to run the example tests, execute them using the following command:

` python3.6 asega.py --contract SomeToken.sol --test ./tests/example/`

For information on options, run the following command:

`python3.6 asega.py --help`


## Example Contracts

The contracts are as follows:

  - ERC20Lib: This is a port of the OpenZeppelin ERC20 Contract into a Library.
  - SafeMath: This is the OpenZeppelin SafeMath Library, unmodified.
  - SomeToken: This is an ERC20 implementation using ERC20Lib.

## The Structure of a Test

A test should be a directory, preferably defined under the /tests directory.
Inside this directory there must be three files:
- contract.spec
- ident.spec
- test.spec

These are the test specification files. There are examples of these files provided in
the examples directory. For more details, a complete explanation of each is below.

## Contract Specification File

The contract specification file should contain a single line. This line describes
the contract to be deployed, and the constructor arguments to be passed. The
example specification file is as below:

`SomeToken:[$owner,$failsafe,100]`

This will instatiate the example constructor:

```
constructor(address _owner,address _failsafe, uint256 supply)
public {
  failsafe = _failsafe;
  owner = _owner;
  token.mint(owner,supply);
}
```
In general the syntax is:

`contract:[args]`

This syntax described as words is as follows:
Deploy the contract named SomeToken with the constructor arguments as the
address of the test identity named `owner` and a failsafe account defined
with the address of the test identity `failsafe`, and an initial balance of
`100` tokens.

## The Identity Specification File

The identity specification file describes the identities that should be built
for this test. These identities are proxy contracts that will be deployed and
will forward all calls to the target contract. In this way a single account
may be used to issue commands as any number of desired identities. IE `msg.sender`
will become the address of the proxy during tests.

The example identity file is as follows:

```
dev:SomeToken
None:SomeToken
owner:SomeToken
failsafe:SomeToken
token1:SomeToken
token2:SomeToken
```
In general the syntax is:

`name:contract`

The syntax says create a proxy that may be referenced by `name` forwards calls
to `contract`. These identities may be named anything. The contract must be the
same contract as the one named in the contract.spec file. The dev identity is a
special identity that is the external account from which all calls originate. The
None identity is an identity that holds no special priveledge. This identity may be used for all reads of state ( `eth_call`). This makes reading the tests much easier.

## The Test Specification File

The test specification file encodes the actual tests to be run. This file may
reference identities from the iden.spec file and all calls are forwarded to the
contract named in the contract.spec file. There are two types of tests calls
`set` and `assert`. This syntax is described below:

`set:ident_to_act_as_caller:contract_method_to_call:arg1,arg2,etc:expected_result`


Examples:

`assert:None:balanceOf:owner:100`

`set:owner:transfer:0x00a329c0648769a73afac7f9381e08fb43dbea72,1:True`

The first test is a read operation and the second a transaction operation.

### The `set` Command Syntax

`set:owner:transfer:0x00a329c0648769a73afac7f9381e08fb43dbea72,1:True`

This test will execute the contract method defined below:

```
  function transfer(address to, uint256 value)
  public
  notPaused
  returns (bool) {
    token.transfer(msg.sender, to, value);
    return true;
  }
```

This transaction will occur with the `msg.sender` as the address of the test identity
`owner`, the `to` argument as the address `0x00a329c0648769a73afac7f9381e08fb43dbea72`
and the `value` argument as 1, with the expected result that the transaction will
succeed. If this call had been as follows:

`set:owner:transfer:0x00a329c0648769a73afac7f9381e08fb43dbea72,1:False`

We would expect this transaction to fail. Notice the change of `True` to `False`.
We can also refernece test identities as arguments as follows:

`set:owner:transfer:$token1,1:True`

Where this call will transfer tokens from the `owner` ident to the `token1` ident.

We can even perform actions that use matching filters on identities as follows:

`set:owner:transfer:$!owner,1:True`

This call will transfer one token to every identity defined in the ident.spec file that is not the `owner`.

We can call all identities as `$*`. For example:

`set:owner:transfer:$*,1:True`

This will transfer one token to all identities defined in the ident.spec file, including the owner.

We can even cause calls to originate from multiple identities in the same way:

`set:$!owner:transfer:$owner,1:True`

This says transfer 1 token to the owner from every account that is not the owner.

We can also wilddcard the caller as follows:

`set:$*:transfer:$owner,1:True`

This says have all identities send one token to the owner.

We can even perform multiple wildcard opreators in the same line:

`set:$*:transfer:$*,1:True`

This says have every identity tranfer to every other idenitty one token.
The tests will calculate all permutations of the arguments and call them each once.

### The `assert` Command Syntax

`assert:None:balanceOf:$owner:100`

This test says assert that the balance of the account named `owner` has a balance of
100 tokens. The `None` account is used to call assert statements as an indicator that
the calling entity need not hold any priveledged role in the contract to read this
information. `None` is essentially equivalent to anyone can call this method, in this
way. This is purely for readbility though, and has no acutual meaning to the program.

All operations defined by `set` can be done with `assert`. The only difference is that
while a transaction may only fail or succeed (hence the `True` and `False` outomes for all `set` operations) an `eth_call` may have any arbitraty output.

Other examples include:

`assert:None:balanceOf:$!owner:100`

Assert the balance of every account that is not the owner is 100

`assert:None:balanceOf:$*:100`

Assert the balance of every account is 100

## Next Features and Known Bugs

The core syntax is still fragile and will break on comparisons of any types other than address, uint256, and uint8 for return types on `assert` calls. The line number
of the test that failed is not printed correctly at this time. I am sure there are
many others, but these are the big ones right now.

This system will be stabalized and have added features when time permits. If you
want to contribute, please open an issue on what you would like to do, and we can
discuss. This is just a side project that was built to speed up testing for a
specific project, but it was so useful, we decided to let the world have it.
