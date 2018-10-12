#SYNTAX EXAMPLE
#<set>:<callerName>:<methodName>:<arg1>,<arg2>:<True:False>
#<assert>:<callerName>:<methodName>:<arg1>,<arg2>:<returnValue>
#arguments may reference a callerAddress by placing a $ in front of callerName
#you may select all callers to perform this action by setting $* as callerName
#you can select all but one caller by setting caller as $!<callerName>
#the same logic works for $ prefixed arguments
#if using $* or $!, all permutations of ident and args will be called

#BASE STATE TESTS
    #assert that owner is owner
    assert:None:isOwner:$owner:True
    #assert that no one else is owner
    assert:None:isOwner:$!owner:False
    #assert the failsafe is failsafe
    assert:None:isFailsafe:$failsafe:True
    #assert that no one else is failsafe
    assert:None:isFailsafe:$!failsafe:False
    #assert that everyone balance except onwer is zero
    assert:None:balanceOf:$!owner:0

#VERIFY OWNER AND FAILSAFE ABILITY TO SET OWNER AND FAILSAFE
    #owner can set owner
    set:owner:setOwner:$owner:True
    #failsafe can set owner
    set:failsafe:setOwner:$owner:True
    #owner can not set failsafe
    set:owner:setFailsafe:$owner:False
    #failsafe can set failsafe
    set:failsafe:setFailsafe:$failsafe:True

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

#TEST CONTRACT PAUSE
    assert:None:isPaused::False
    set:owner:pause::True
    assert:None:isPaused::True

#TEST ALL METHODS LOCKED IN PAUSE
    set:token1:transfer:$token2,1:False
    set:token1:approve:$token2,1:False
    set:token2:transferFrom:$token1,$token2,1:False
    set:token1:increaseAllowance:$token2,1:False
    set:token1:decreaseAllowance:$token2,1:False

#TEST ONLY FAILSAFE CAN UNPAUSE
    assert:None:isPaused::True
    set:$!failsafe:unpause::False
    set:failsafe:unpause::True
    assert:None:isPaused::False

#TEST LOCKDOWN NOTE: THIS MUST BE DONE LAST!
    assert:None:isPaused::False
    set:$!failsafe:lockForever::False
    set:failsafe:lockForever::True
    assert:None:isPaused::True
    set:$*:unpause::False
    assert:None:isPaused::True
