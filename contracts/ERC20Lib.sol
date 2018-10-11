pragma solidity ^0.4.24;

import "./SafeMath.sol";

/**
* @dev This is a library based implementation of the ERC20 token standard.
* This library allows all values to be set by interface logic. This includes
* the ability to set msg.sender. This allows two distinct advantages:
*  - Access control logic may be layered without the need to change the
*    core logic of the ERC20 system in any way.
*  - Tokens that require administrative action, under some conditions,
*    may take administrative action on an account, without having to
*    create fragile backdoors into the transfer logic of the token. This
*    system makes such administrative priveledge clear, apparent, and
*    more easily auditable to ensure reasonable limitations of power.
*/
library ERC20Lib {


  ////////////////////////////////////////////////////////////////////////////
  //Imports

  /**
  * @dev Prevents underflow and overflow attacks..
  */
  using SafeMath for uint256;
  ///////////////////////////////////////////////////////////////////////////


  ////////////////////////////////////////////////////////////////////////////
  //Events

  /**
  * @dev Transfer event emitted in 3 cases; transfers, minting, and burning.
  * for transfers, all fields set as normal
  * for minting from is set to address(0)
  * for burning is set to address(0)
  */
  event Transfer(address indexed from, address indexed to, uint256 value);

  /**
  * @dev Specifies an approval being granted from an owner to a spender
  * for the amount specified.
  */
  event Approval(address indexed owner, address indexed spender, uint256 value);
  ////////////////////////////////////////////////////////////////////////////

  ////////////////////////////////////////////////////////////////////////////
  //Declarations

  /**
  * @dev Struct like representation of ERC20 state vairiables.
  * this allows the ERC20 logic to become a library under using for syntax
  */
  struct Token{
    mapping (address => uint256) _balances;
    mapping (address => mapping (address => uint256)) _allowed;
    uint256 _totalSupply;
  }
  ////////////////////////////////////////////////////////////////////////////


  ////////////////////////////////////////////////////////////////////////////
  //Logic

  /**
  * @dev Returns the total supply of the token.
  */
  function totalSupply(Token storage self)
  internal
  view
  returns (uint256) {
    return self._totalSupply;
  }

  /**
  * @dev Returns the balance of an account.
  */
  function balances(Token storage self, address account)
  internal
  view
  returns (uint256) {
    return self._balances[account];
  }

  /**
  * @dev Returns the total allowance from the account to the spender..
  */
  function allowance(Token storage self, address account, address spender)
  internal
  view
  returns (uint256) {
    return self._allowed[account][spender];
  }

  /**
  * @dev Issues an allowance from an account to another.
  */
  function approve(Token storage self, address sender, address spender, uint256 value)
  internal {
    require(spender != address(0));
    self._allowed[sender][spender] = value;
    emit Approval(sender, spender, value);
  }

  /**
  * @dev Cause a transfer to occur based on an existing allowance.
  */
  function transferFrom(Token storage self, address sender, address from, address to, uint256 value)
  internal {
    require(value <= self._allowed[from][sender]);
    self._allowed[from][sender] = self._allowed[from][sender].sub(value);
    transfer(self,from, to, value);
  }

  /**
  * @dev Increase the allowance from one account to another. Prevents
  * change allowance attack.
  */
  function increaseAllowance(Token storage self, address sender, address spender, uint256 addedValue)
  internal {
    require(spender != address(0));
    self._allowed[sender][spender] = self._allowed[sender][spender].add(addedValue);
    emit Approval(sender, spender, self._allowed[sender][spender]);
  }

  /**
  * @dev Decrease the allowance from one account to another. Prevents
  * the change allowance attack.
  */
  function decreaseAllowance(Token storage self, address sender, address spender, uint256 subtractedValue)
  internal {
    require(spender != address(0));
    self._allowed[sender][spender] = self._allowed[sender][spender].sub(subtractedValue);
    emit Approval(sender, spender, self._allowed[sender][spender]);
  }

  /**
  * @dev Transfer tokens from one account to another.
  */
  function transfer(Token storage self, address sender, address to, uint256 value)
  internal {
    require(value <= self._balances[sender]);
    require(to != address(0));
    self._balances[sender] = self._balances[sender].sub(value);
    self._balances[to] = self._balances[to].add(value);
    emit Transfer(sender, to, value);
  }

  /**
  * @dev Mint new tokens to an account.
  */
  function mint(Token storage self, address account, uint256 value)
  internal {
    require(account != 0);
    self._totalSupply = self._totalSupply.add(value);
    self._balances[account] = self._balances[account].add(value);
    emit Transfer(address(0), account, value);
  }

  /**
  * @dev Burn tokens from an account.
  */
  function burn(Token storage self, address account, uint256 value)
  internal {
    require(account != 0);
    require(value <= self._balances[account]);
    self._totalSupply = self._totalSupply.sub(value);
    self._balances[account] = self._balances[account].sub(value);
    emit Transfer(account, address(0), value);
  }
  ////////////////////////////////////////////////////////////////////////////

}
