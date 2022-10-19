from .libraries import Tick, TickMath, SwapMath, FullMath, LiquidityMath
from .libraries import Position, SqrtPriceMath, SafeMath

from .libraries.Account import Account
from .libraries.Shared import *
from dataclasses import dataclass


@dataclass
class Slot0:
    ## the current price
    sqrtPriceX96: int
    ## the current tick
    tick: int
    ## the current protocol fee as a percentage of the swap fee taken on withdrawal
    ## represented as an integer denominator (1#x)%
    feeProtocol: int


@dataclass
class ModifyPositionParams:
    ## the address that owns the position
    owner: int
    ## the lower and upper tick of the position
    tickLower: int
    tickUpper: int
    ## any change in liquidity
    liquidityDelta: int


@dataclass
class SwapCache:
    ## the protocol fee for the input token
    feeProtocol: int
    ## liquidity at the beginning of the swap
    liquidityStart: int


## the top level state of the swap, the results of which are recorded in storage at the end
@dataclass
class SwapState:
    ## the amount remaining to be swapped in#out of the input#output asset
    amountSpecifiedRemaining: int
    ## the amount already swapped out#in of the output#input asset
    amountCalculated: int
    ## current sqrt(price)
    sqrtPriceX96: int
    ## the tick associated with the current price
    tick: int
    ## the global fee growth of the input token
    feeGrowthGlobalX128: int
    ## amount of input token paid as protocol fee
    protocolFee: int
    ## the current liquidity in range
    liquidity: int

    ## list of ticks crossed during the swap
    ticksCrossed: list


@dataclass
class StepComputations:
    ## the price at the beginning of the step
    sqrtPriceStartX96: int
    ## the next tick to swap to from the current tick in the swap direction
    tickNext: int
    ## whether tickNext is initialized or not
    initialized: bool
    ## sqrt(price) for the next tick (1#0)
    sqrtPriceNextX96: int
    ## how much is being swapped in in this step
    amountIn: int
    ## how much is being swapped out
    amountOut: int
    ## how much fee is being paid in
    feeAmount: int


@dataclass
class ProtocolFees:
    token0: int
    token1: int


class UniswapPool(Account):

    # Constructor
    def __init__(self, token0, token1, fee, tickSpacing, ledger):
        checkInputTypes(string=(token0, token1), uint24=(fee), int24=(tickSpacing))
        # Contract storage variables
        super().__init__("UniswapPool", [token0, token1], [0, 0])
        self.token0 = token0
        self.token1 = token1
        self.fee = fee
        self.tickSpacing = tickSpacing
        self.maxLiquidityPerTick = Tick.tickSpacingToMaxLiquidityPerTick(tickSpacing)

        # Initialize remaining storage variables
        self.slot0 = Slot0(0, 0, 0)
        self.feeGrowthGlobal0X128 = 0
        self.feeGrowthGlobal1X128 = 0
        self.protocolFees = ProtocolFees(0, 0)
        self.liquidity = 0
        # dict ( int24 => Tick.Info)
        self.ticks = dict()
        self.positions = dict()

        self.ledger = ledger

    ### @dev Common checks for valid tick inputs.
    def checkTicks(tickLower, tickUpper):
        checkInputTypes(int24=(tickLower, tickUpper))
        assert tickLower < tickUpper, "TLU"
        assert tickLower >= TickMath.MIN_TICK, "TLM"
        assert tickUpper <= TickMath.MAX_TICK, "TUM"

    ### @notice Sets the initial price for the pool
    ### @dev Price is represented as a sqrt(amountToken1/amountToken0) Q64.96 value
    ### @param sqrtPriceX96 the initial sqrt price of the pool as a Q64.96
    def initialize(self, sqrtPriceX96):
        checkInputTypes(uint160=(sqrtPriceX96))
        assert self.slot0.sqrtPriceX96 == 0, "AI"

        tick = TickMath.getTickAtSqrtRatio(sqrtPriceX96)

        self.slot0 = Slot0(
            sqrtPriceX96,
            tick,
            0,
        )

    ## @dev Effect some changes to a position
    ## @param params the position details and the change to the position's liquidity to effect
    ## @return position a storage pointer referencing the position with the given owner and tick range
    ## @return amount0 the amount of token0 owed to the pool, negative if the pool should pay the recipient
    ## @return amount1 the amount of token1 owed to the pool, negative if the pool should pay the recipient
    def _modifyPosition(self, params):
        checkInputTypes(
            accounts=(params.owner),
            int24=(params.tickLower, params.tickUpper),
            int128=(params.liquidityDelta),
        )
        UniswapPool.checkTicks(params.tickLower, params.tickUpper)

        # Initialize values
        amount0 = amount1 = 0

        position = self._updatePosition(
            params.owner,
            params.tickLower,
            params.tickUpper,
            params.liquidityDelta,
            self.slot0.tick,
        )

        if params.liquidityDelta != 0:
            if self.slot0.tick < params.tickLower:
                ## current tick is below the passed range; liquidity can only become in range by crossing from left to
                ## right, when we'll need _more_ token0 (it's becoming more valuable) so user must provide it
                amount0 = SqrtPriceMath.getAmount0DeltaHelper(
                    TickMath.getSqrtRatioAtTick(params.tickLower),
                    TickMath.getSqrtRatioAtTick(params.tickUpper),
                    params.liquidityDelta,
                )
            elif self.slot0.tick < params.tickUpper:
                ## current tick is inside the passed range
                amount0 = SqrtPriceMath.getAmount0DeltaHelper(
                    self.slot0.sqrtPriceX96,
                    TickMath.getSqrtRatioAtTick(params.tickUpper),
                    params.liquidityDelta,
                )
                amount1 = SqrtPriceMath.getAmount1DeltaHelper(
                    TickMath.getSqrtRatioAtTick(params.tickLower),
                    self.slot0.sqrtPriceX96,
                    params.liquidityDelta,
                )
                self.liquidity = LiquidityMath.addDelta(
                    self.liquidity, params.liquidityDelta
                )
            else:
                ## current tick is above the passed range; liquidity can only become in range by crossing from right to
                ## left, when we'll need _more_ token1 (it's becoming more valuable) so user must provide it
                amount1 = SqrtPriceMath.getAmount1DeltaHelper(
                    TickMath.getSqrtRatioAtTick(params.tickLower),
                    TickMath.getSqrtRatioAtTick(params.tickUpper),
                    params.liquidityDelta,
                )

        return (position, amount0, amount1)

    ### @dev Gets and updates a position with the given liquidity delta
    ### @param owner the owner of the position
    ### @param tickLower the lower tick of the position's tick range
    ### @param tickUpper the upper tick of the position's tick range
    ### @param tick the current tick, passed to avoid sloads
    def _updatePosition(self, owner, tickLower, tickUpper, liquidityDelta, tick):
        checkInputTypes(
            accounts=(owner),
            int24=(tickLower, tickUpper, tick),
            int128=(liquidityDelta),
        )
        # This will create a position if it doesn't exist
        position = Position.get(self.positions, owner, tickLower, tickUpper)

        # Initialize values
        flippedLower = flippedUpper = False

        ## if we need to update the ticks, do it
        if liquidityDelta != 0:
            flippedLower = Tick.update(
                self.ticks,
                tickLower,
                tick,
                liquidityDelta,
                self.feeGrowthGlobal0X128,
                self.feeGrowthGlobal1X128,
                False,
                self.maxLiquidityPerTick,
            )
            flippedUpper = Tick.update(
                self.ticks,
                tickUpper,
                tick,
                liquidityDelta,
                self.feeGrowthGlobal0X128,
                self.feeGrowthGlobal1X128,
                True,
                self.maxLiquidityPerTick,
            )

        if flippedLower:
            assert tickLower % self.tickSpacing == 0  ## ensure that the tick is spaced
        if flippedUpper:
            assert tickUpper % self.tickSpacing == 0  ## ensure that the tick is spaced

        (feeGrowthInside0X128, feeGrowthInside1X128) = Tick.getFeeGrowthInside(
            self.ticks,
            tickLower,
            tickUpper,
            tick,
            self.feeGrowthGlobal0X128,
            self.feeGrowthGlobal1X128,
        )

        Position.update(
            position, liquidityDelta, feeGrowthInside0X128, feeGrowthInside1X128
        )

        ## clear any tick data that is no longer needed
        if liquidityDelta < 0:
            if flippedLower:
                Tick.clear(self.ticks, tickLower)
            if flippedUpper:
                Tick.clear(self.ticks, tickUpper)
        return position

    ## @notice Adds liquidity for the given recipient/tickLower/tickUpper position
    ## @dev The final amounts calculated are automatically transferred from the swapper
    ## to the pool and vice verse. The amount of token0/token1 due depends
    ## on tickLower, tickUpper, the amount of liquidity, and the current price.
    ## @param recipient The address for which the liquidity will be created
    ## @param tickLower The lower tick of the position in which to add liquidity
    ## @param tickUpper The upper tick of the position in which to add liquidity
    ## @param amount The amount of liquidity to mint
    ## @return amount0 The amount of token0 that was paid to mint the given amount of liquidity.
    ## @return amount1 The amount of token1 that was paid to mint the given amount of liquidity.
    def mint(self, recipient, tickLower, tickUpper, amount):
        checkInputTypes(
            accounts=(recipient), int24=(tickLower, tickUpper), uint128=(amount)
        )
        assert amount > 0

        (_, amount0Int, amount1Int) = self._modifyPosition(
            ModifyPositionParams(recipient, tickLower, tickUpper, amount)
        )

        amount0 = toUint256(abs(amount0Int))
        amount1 = toUint256(abs(amount1Int))

        # Transfer tokens - including safety checks
        self.ledger.transferToken(recipient, self, self.token0, amount0)
        self.ledger.transferToken(recipient, self, self.token1, amount1)

        return (amount0, amount1)

    ## @notice Collects tokens owed to a position
    ## @dev Does not recompute fees earned, which must be done either via mint or burn of any amount of liquidity.
    ## Collect must be called by the position owner. To withdraw only token0 or only token1, amount0Requested or
    ## amount1Requested may be set to zero. To withdraw all tokens owed, caller may pass any value greater than the
    ## actual tokens owed, e.g. type(uint128).max. Tokens owed may be from accumulated swap fees or burned liquidity.
    ## @param recipient The address which should receive the fees collected
    ## @param tickLower The lower tick of the position for which to collect fees
    ## @param tickUpper The upper tick of the position for which to collect fees
    ## @param amount0Requested How much token0 should be withdrawn from the fees owed
    ## @param amount1Requested How much token1 should be withdrawn from the fees owed
    ## @return amount0 The amount of fees collected in token0
    ## @return amount1 The amount of fees collected in token1
    def collect(
        self, recipient, tickLower, tickUpper, amount0Requested, amount1Requested
    ):
        checkInputTypes(
            accounts=(recipient),
            int24=(tickLower, tickUpper),
            uint128=(amount0Requested, amount1Requested),
        )
        # Add this check to prevent creating a new position if the position doesn't exist or it's empty
        position = Position.assertPositionExists(
            self.positions, recipient, tickLower, tickUpper
        )

        amount0 = (
            position.tokensOwed0
            if (amount0Requested > position.tokensOwed0)
            else amount0Requested
        )
        amount1 = (
            position.tokensOwed1
            if (amount1Requested > position.tokensOwed1)
            else amount1Requested
        )

        if amount0 > 0:
            position.tokensOwed0 -= amount0
            self.ledger.transferToken(self, recipient, self.token0, amount0)
        if amount1 > 0:
            position.tokensOwed1 -= amount1
            self.ledger.transferToken(self, recipient, self.token1, amount1)

        return (recipient, tickLower, tickUpper, amount0, amount1)

    ## @notice Burn liquidity from the sender and account tokens owed for the liquidity to the position
    ## @dev Can be used to trigger a recalculation of fees owed to a position by calling with an amount of 0
    ## @dev Fees must be collected separately via a call to #collect
    ## @param tickLower The lower tick of the position for which to burn liquidity
    ## @param tickUpper The upper tick of the position for which to burn liquidity
    ## @param amount How much liquidity to burn
    ## @return amount0 The amount of token0 sent to the recipient
    ## @return amount1 The amount of token1 sent to the recipient
    def burn(self, recipient, tickLower, tickUpper, amount):
        checkInputTypes(
            accounts=(recipient), int24=(tickLower, tickUpper), uint128=(amount)
        )

        # Add check if the position exists - when poking an uninitialized position it can be that
        # getFeeGrowthInside finds a non-initialized tick before Position.update reverts.
        Position.assertPositionExists(self.positions, recipient, tickLower, tickUpper)

        # Added extra recipient input variable to mimic msg.sender
        (position, amount0Int, amount1Int) = self._modifyPosition(
            ModifyPositionParams(recipient, tickLower, tickUpper, -amount)
        )

        # Mimic conversion to uint256
        amount0 = abs(-amount0Int) & (2**256 - 1)
        amount1 = abs(-amount1Int) & (2**256 - 1)

        if amount0 > 0 or amount1 > 0:
            position.tokensOwed0 += amount0
            position.tokensOwed1 += amount1

        return (recipient, tickLower, tickUpper, amount, amount0, amount1)

    ## @notice Swap token0 for token1, or token1 for token0
    ## @dev The tokens are automatically transferred at the end of the swapping function.
    ## @param recipient The address to receive the output of the swap
    ## @param zeroForOne The direction of the swap, true for token0 to token1, false for token1 to token0
    ## @param amountSpecified The amount of the swap, which implicitly configures the swap as exact input (positive), or exact output (negative)
    ## @param sqrtPriceLimitX96 The Q64.96 sqrt price limit. If zero for one, the price cannot be less than this
    ## value after the swap. If one for zero, the price cannot be greater than this value after the swap
    ## @return amount0 The delta of the balance of token0 of the pool, exact when negative, minimum when positive
    ## @return amount1 The delta of the balance of token1 of the pool, exact when negative, minimum when positive
    def swap(self, recipient, zeroForOne, amountSpecified, sqrtPriceLimitX96):
        checkInputTypes(
            accounts=(recipient),
            bool=(zeroForOne),
            int256=(amountSpecified),
            uint160=(sqrtPriceLimitX96),
        )
        assert amountSpecified != 0, "AS"

        slot0Start = self.slot0

        if zeroForOne:
            assert (
                sqrtPriceLimitX96 < slot0Start.sqrtPriceX96
                and sqrtPriceLimitX96 > TickMath.MIN_SQRT_RATIO
            ), "SPL"
        else:
            assert (
                sqrtPriceLimitX96 > slot0Start.sqrtPriceX96
                and sqrtPriceLimitX96 < TickMath.MAX_SQRT_RATIO
            ), "SPL"

        feeProtocol = (
            (slot0Start.feeProtocol % 16)
            if zeroForOne
            else (slot0Start.feeProtocol >> 4)
        )

        cache = SwapCache(feeProtocol, self.liquidity)

        exactInput = amountSpecified > 0

        state = SwapState(
            amountSpecified,
            0,
            slot0Start.sqrtPriceX96,
            slot0Start.tick,
            self.feeGrowthGlobal0X128 if zeroForOne else self.feeGrowthGlobal1X128,
            0,
            cache.liquidityStart,
            [],
        )

        while (
            state.amountSpecifiedRemaining != 0
            and state.sqrtPriceX96 != sqrtPriceLimitX96
        ):
            step = StepComputations(0, 0, 0, 0, 0, 0, 0)
            step.sqrtPriceStartX96 = state.sqrtPriceX96

            (step.tickNext, step.initialized) = self.nextTick(state.tick, zeroForOne)

            ## get the price for the next tick
            step.sqrtPriceNextX96 = TickMath.getSqrtRatioAtTick(step.tickNext)

            ## compute values to swap to the target tick, price limit, or point where input#output amount is exhausted
            if zeroForOne:
                sqrtRatioTargetX96 = (
                    sqrtPriceLimitX96
                    if step.sqrtPriceNextX96 < sqrtPriceLimitX96
                    else step.sqrtPriceNextX96
                )
            else:
                sqrtRatioTargetX96 = (
                    sqrtPriceLimitX96
                    if step.sqrtPriceNextX96 > sqrtPriceLimitX96
                    else step.sqrtPriceNextX96
                )

            (
                state.sqrtPriceX96,
                step.amountIn,
                step.amountOut,
                step.feeAmount,
            ) = SwapMath.computeSwapStep(
                state.sqrtPriceX96,
                sqrtRatioTargetX96,
                state.liquidity,
                state.amountSpecifiedRemaining,
                self.fee,
            )
            if exactInput:
                state.amountSpecifiedRemaining -= step.amountIn + step.feeAmount
                state.amountCalculated = SafeMath.subInts(
                    state.amountCalculated, step.amountOut
                )
            else:
                state.amountSpecifiedRemaining += step.amountOut
                state.amountCalculated = SafeMath.addInts(
                    state.amountCalculated, step.amountIn + step.feeAmount
                )

            ## if the protocol fee is on, calculate how much is owed, decrement feeAmount, and increment protocolFee
            if cache.feeProtocol > 0:
                delta = abs(step.feeAmount // cache.feeProtocol)
                step.feeAmount -= delta
                state.protocolFee += delta & (2**128 - 1)

            ## update global fee tracker
            if state.liquidity > 0:
                state.feeGrowthGlobalX128 += FullMath.mulDiv(
                    step.feeAmount, FixedPoint128_Q128, state.liquidity
                )
                # Addition can overflow in Solidity - mimic it
                state.feeGrowthGlobalX128 = toUint256(state.feeGrowthGlobalX128)

            ## shift tick if we reached the next price
            if state.sqrtPriceX96 == step.sqrtPriceNextX96:
                ## if the tick is initialized, run the tick transition
                ## @dev: here is where we should handle the case of an uninitialized boundary tick
                if step.initialized:
                    liquidityNet = Tick.cross(
                        self.ticks,
                        step.tickNext,
                        state.feeGrowthGlobalX128
                        if zeroForOne
                        else self.feeGrowthGlobal0X128,
                        self.feeGrowthGlobal1X128
                        if zeroForOne
                        else state.feeGrowthGlobalX128,
                    )
                    ## if we're moving leftward, we interpret liquidityNet as the opposite sign
                    ## safe because liquidityNet cannot be type(int128).min
                    if zeroForOne:
                        liquidityNet = -liquidityNet

                    state.liquidity = LiquidityMath.addDelta(
                        state.liquidity, liquidityNet
                    )

                state.tick = (step.tickNext - 1) if zeroForOne else step.tickNext
            elif state.sqrtPriceX96 != step.sqrtPriceStartX96:
                ## recompute unless we're on a lower tick boundary (i.e. already transitioned ticks), and haven't moved
                state.tick = TickMath.getTickAtSqrtRatio(state.sqrtPriceX96)

        ## End of swap loop
        ## update tick
        if state.tick != slot0Start.tick:
            self.slot0.sqrtPriceX96 = state.sqrtPriceX96
            self.slot0.tick = state.tick
        else:
            ## otherwise just update the price
            self.slot0.sqrtPriceX96 = state.sqrtPriceX96

        ## update liquidity if it changed
        if cache.liquidityStart != state.liquidity:
            self.liquidity = state.liquidity

        ## update fee growth global and, if necessary, protocol fees
        ## overflow is acceptable, protocol has to withdraw before it hits type(uint128).max fees

        if zeroForOne:
            self.feeGrowthGlobal0X128 = state.feeGrowthGlobalX128
            if state.protocolFee > 0:
                self.protocolFees.token0 += state.protocolFee
        else:
            self.feeGrowthGlobal1X128 = state.feeGrowthGlobalX128
            if state.protocolFee > 0:
                self.protocolFees.token1 += state.protocolFee

        (amount0, amount1) = (
            (amountSpecified - state.amountSpecifiedRemaining, state.amountCalculated)
            if (zeroForOne == exactInput)
            else (
                state.amountCalculated,
                amountSpecified - state.amountSpecifiedRemaining,
            )
        )

        ## do the transfers and collect payment
        if zeroForOne:
            if amount1 < 0:
                self.ledger.transferToken(self, recipient, self.token1, abs(amount1))
            balanceBefore = self.balances[self.token0]
            self.ledger.transferToken(recipient, self, self.token0, abs(amount0))
            assert balanceBefore + abs(amount0) == self.balances[self.token0], "IIA"
        else:
            if amount0 < 0:
                self.ledger.transferToken(self, recipient, self.token0, abs(amount0))

            balanceBefore = self.balances[self.token1]
            self.ledger.transferToken(recipient, self, self.token1, abs(amount1))
            assert balanceBefore + abs(amount1) == self.balances[self.token1], "IIA"

        return (
            recipient,
            amount0,
            amount1,
            state.sqrtPriceX96,
            state.liquidity,
            state.tick,
        )

    ### @notice Set the denominator of the protocol's % share of the fees
    ### @param feeProtocol0 new protocol fee for token0 of the pool
    ### @param feeProtocol1 new protocol fee for token1 of the pool
    def setFeeProtocol(self, feeProtocol0, feeProtocol1):
        checkInputTypes(uint8=(feeProtocol0, feeProtocol1))
        assert (feeProtocol0 == 0 or (feeProtocol0 >= 4 and feeProtocol0 <= 10)) and (
            feeProtocol1 == 0 or (feeProtocol1 >= 4 and feeProtocol1 <= 10)
        )

        feeProtocolOld = self.slot0.feeProtocol
        feeProtocolNew = feeProtocol0 + (feeProtocol1 << 4)
        # Health check
        checkUInt8(feeProtocolNew)
        self.slot0.feeProtocol = feeProtocolNew
        return (feeProtocolOld % 16, feeProtocolOld >> 4, feeProtocol0, feeProtocol1)

    ### @notice Collect the protocol fee accrued to the pool
    ### @param recipient The address to which collected protocol fees should be sent
    ### @param amount0Requested The maximum amount of token0 to send, can be 0 to collect fees in only token1
    ### @param amount1Requested The maximum amount of token1 to send, can be 0 to collect fees in only token0
    ### @return amount0 The protocol fee collected in token0
    ### @return amount1 The protocol fee collected in token1
    def collectProtocol(self, recipient, amount0Requested, amount1Requested):
        checkInputTypes(
            accounts=(recipient), uint128=(amount0Requested, amount1Requested)
        )
        amount0 = (
            self.protocolFees.token0
            if amount0Requested > self.protocolFees.token0
            else amount0Requested
        )
        amount1 = (
            self.protocolFees.token1
            if amount1Requested > self.protocolFees.token1
            else amount1Requested
        )

        if amount0 > 0:
            if amount0 == self.protocolFees.token0:
                amount0 -= 1  ##ensure that the slot is not cleared, for gas savings
            self.protocolFees.token0 -= amount0
            self.ledger.transferToken(self, recipient, self.token0, amount0)

        if amount1 > 0:
            if amount1 == self.protocolFees.token1:
                amount1 -= 1  ## ensure that the slot is not cleared, for gas savings
            self.protocolFees.token1 -= amount1
            self.ledger.transferToken(self, recipient, self.token1, amount1)

        return recipient, amount0, amount1

    ### @notice It is assumed that the keys are within [MIN_TICK , MAX_TICK], which should always be the case.
    ### We don't run the risk of overshooting tickNext (out of boundaries) as long as ticks (keys) have been initialized
    ### within the boundaries. However, if there is no initialized tick to the left or right we will return the next boundary
    ### Then we need to return the initialized bool to indicate that we are at the boundary and it is not an initalized tick.
    ### @param self The mapping in which to compute the next initialized tick
    ### @param tick The starting tick
    ### @param lte Whether to search for the next initialized tick to the left (less than or equal to the starting tick)
    ### @return Next tick with liquidity to be used in the swap function.
    def nextTick(self, tick, lte):
        checkInputTypes(int24=(tick), bool=(lte))

        keyList = list(self.ticks.keys())

        # If tick doesn't exist in the mapping we fake it (easier than searching for nearest value). This is probably not the
        # best way, but it is a simple and intuitive way to reproduce the behaviour of the logic.
        if not self.ticks.__contains__(tick):
            keyList += [tick]
        sortedKeyList = sorted(keyList)
        indexCurrentTick = sortedKeyList.index(tick)

        if lte:
            # If the current tick is initialized (not faked), we return the current tick
            if self.ticks.__contains__(tick):
                return tick, True
            elif indexCurrentTick == 0:
                # No tick to the left
                return TickMath.MIN_TICK, False
            else:
                nextTick = sortedKeyList[indexCurrentTick - 1]
        else:

            if indexCurrentTick == len(sortedKeyList) - 1:
                # No tick to the right
                return TickMath.MAX_TICK, False
            nextTick = sortedKeyList[indexCurrentTick + 1]

        # Return tick within the boundaries
        return nextTick, True
