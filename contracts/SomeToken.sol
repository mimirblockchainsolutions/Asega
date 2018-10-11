pragma solidity ^0.4.24;

import './ERC20Lib.sol';


contract SomeToken{

  ////////////////////////////////////////////////////////////////////////////
  //Imports
  using ERC20Lib for ERC20Lib.Token;
  ///////////////////////////////////////////////////////////////////////////

  ////////////////////////////////////////////////////////////////////////////
  //Declarations
  ERC20Lib.Token token;
  uint256 eventNonce;
  address failsafe;
  address owner;
  bool paused;
  ////////////////////////////////////////////////////////////////////////////

  ////////////////////////////////////////////////////////////////////////////
  //Constructor
  constructor(address _owner,address _failsafe, uint256 supply)
  public {
    failsafe = _failsafe;
    owner = _owner;
    token.mint(owner,supply);
  }
  ////////////////////////////////////////////////////////////////////////////

  ////////////////////////////////////////////////////////////////////////////
  //Modifiers
  modifier onlyFailsafe(){
    require(msg.sender == failsafe);
    _;
  }

  modifier onlyAdmin(){
    require(msg.sender == owner || msg.sender == failsafe);
    _;
  }

  modifier notPaused(){
    require(!paused);
    _;
  }
  ////////////////////////////////////////////////////////////////////////////

  ////////////////////////////////////////////////////////////////////////////
  //Failsafe Logic
  function isFailsafe(address _failsafe)
  public
  view
  returns (bool){
    return (failsafe == _failsafe);
  }

  function setFailsafe(address _failsafe)
  public
  onlyFailsafe{
    failsafe = _failsafe;
  }
  ////////////////////////////////////////////////////////////////////////////

  ////////////////////////////////////////////////////////////////////////////
  //Owner Logic
  function isOwner(address _owner)
  public
  view
  returns (bool){
    return (owner == _owner);
  }

  function setOwner(address _owner)
  public
  onlyAdmin{
    owner = _owner;
  }
  ////////////////////////////////////////////////////////////////////////////

  ////////////////////////////////////////////////////////////////////////////
  //Pause Logic

  /**
  * @dev Administrative lockdown check.
  **/
  function isPaused()
  public
  view
  returns (bool) {
    return paused;
  }

  /**
  * @dev Locks down all actions except administrative actions. Should be used
  * to address security flaws. If this contract has a critical bug, This method
  * should be called to allow for a hault of operations and a migration to occur
  * If this method is called due to a loss of server keys, it will hault
  * operation until root cause may be found.
  **/
  function pause()
  public
  onlyAdmin
  notPaused
  returns (bool) {
    paused = true;
    return true;
  }

  /**
  * @dev Releases system from administrative lockdown. Requires retrieval of
  * failsafe coldwallet.
  **/
  function unpause()
  public
  onlyFailsafe
  returns (bool) {
    paused = false;
    return true;
  }

  /**
  * @dev Locks down all actions FOREVER! This should only be used in
  * manual contract migration due to critical bug. This will halt all
  *operations and allow a new contract to be built by transfering all balances.
  **/
  function lockForever()
  public
  onlyFailsafe
  returns (bool) {
    pause();
    setOwner(address(this));
    setFailsafe(address(this));
    return true;
  }
  ////////////////////////////////////////////////////////////////////////////

  ////////////////////////////////////////////////////////////////////////////
  //Panic Logic

  /**
  * @dev Lets everyone know if something catastrophic has occured.
  */
  function isBadDay()
  public
  view
  returns (bool) {
    return (isPaused() && (owner == failsafe));
  }
  ////////////////////////////////////////////////////////////////////////////

  ////////////////////////////////////////////////////////////////////////////
  //ERC20Lib Wrappers

  /**
  * @dev These methods act as transparent wrappers around the ERC20Lib.
  */
  function totalSupply()
  public
  view
  returns (uint256) {
    return token.totalSupply();
  }

  function balanceOf(address account)
  public
  view
  returns (uint256) {
    return token.balances(account);
  }

  function allowance(address account, address spender)
  public
  view
  returns (uint256) {
    return token.allowance(account,spender);
  }

  function transfer(address to, uint256 value)
  public
  notPaused
  returns (bool) {
    token.transfer(msg.sender, to, value);
    return true;
  }

  function approve(address spender, uint256 value)
  public
  notPaused
  returns (bool) {
    token.approve(msg.sender,spender,value);
    return true;
  }

  function transferFrom(address from, address to, uint256 value)
  public
  notPaused
  returns (bool) {
    token.transferFrom(msg.sender,from,to,value);
    return true;
  }

  function increaseAllowance(address spender, uint256 addedValue)
  public
  notPaused
  returns (bool) {
    token.increaseAllowance(msg.sender,spender,addedValue);
    return true;
  }

  function decreaseAllowance(address spender, uint256 subtractedValue)
  public
  notPaused
  returns (bool) {
    token.decreaseAllowance(msg.sender,spender,subtractedValue);
    return true;
  }
  ////////////////////////////////////////////////////////////////////////////

}
