from .utilities import *

from ..src.UniswapPool import *
from ..src.libraries.Account import Ledger

from ..src.libraries import SwapMath, TickMath

import copy


@pytest.fixture
def accounts(ledger):
    return getAccountsFromLedger(ledger)


def getAccountsFromLedger(l):
    # list of raw addresses
    return list(l.accounts.keys())


@pytest.fixture
def ledger():
    return createLedger()


def createLedger():
    # Create multiple accounts and fund them with a large amount of tokens. Asymmetrical
    # between token0 and token1 to avoid masking errors.
    accountNames = ["ALICE", "BOB", "CHARLIE", "DENICE", "EVA", "FINN"]
    accounts = [
        [accountName, TEST_TOKENS, [MAX_INT256 // 1000, MAX_INT256 // 2000]]
        for accountName in accountNames
    ]
    ledger = Ledger(accounts)
    return ledger


@pytest.fixture
def TEST_POOLS():
    return UniswapPool


def createPool(TEST_POOLS, feeAmount, tickSpacing, ledger):
    feeAmount = feeAmount
    pool = TEST_POOLS(TEST_TOKENS[0], TEST_TOKENS[1], feeAmount, tickSpacing, ledger)
    minTick = getMinTick(tickSpacing)
    maxTick = getMaxTick(tickSpacing)
    return pool, minTick, maxTick, feeAmount, tickSpacing


@pytest.fixture
def createPoolMedium(TEST_POOLS, ledger):
    return createPool(
        TEST_POOLS, FeeAmount.MEDIUM, TICK_SPACINGS[FeeAmount.MEDIUM], ledger
    )


@pytest.fixture
def createPoolLow(TEST_POOLS, ledger):
    return createPool(TEST_POOLS, FeeAmount.LOW, TICK_SPACINGS[FeeAmount.LOW], ledger)


@pytest.fixture
def initializedMediumPool(createPoolMedium, accounts):
    pool, minTick, maxTick, _, _ = createPoolMedium
    pool.initialize(encodePriceSqrt(1, 10))
    pool.mint(accounts[0], minTick, maxTick, 3161)
    return createPoolMedium


@pytest.fixture
def initializedLowPoolCollect(createPoolLow):
    pool, _, _, _, _ = createPoolLow
    pool.initialize(encodePriceSqrt(1, 1))
    return createPoolLow


def test_constructor(createPoolMedium):
    print("constructor initializes immutables")
    pool, _, _, _, _ = createPoolMedium
    assert pool.token0 == TEST_TOKENS[0]
    assert pool.token1 == TEST_TOKENS[1]
    assert pool.fee == FeeAmount.MEDIUM
    assert pool.tickSpacing == TICK_SPACINGS[FeeAmount.MEDIUM]


# Initialize
def test_fails_alreadyInitialized(createPoolMedium):
    print("fails if already initialized")
    pool, _, _, _, _ = createPoolMedium
    pool.initialize(encodePriceSqrt(1, 1))
    tryExceptHandler(pool.initialize, "AI", encodePriceSqrt(1, 1))


def test_fails_lowStartingPrice(createPoolMedium):
    pool, _, _, _, _ = createPoolMedium
    print("fails if already initialized")
    tryExceptHandler(pool.initialize, "R", 1)
    tryExceptHandler(pool.initialize, "R", TickMath.MIN_SQRT_RATIO - 1)


def test_fails_highStartingPrice(createPoolMedium):
    print("fails if already initialized")
    pool, _, _, _, _ = createPoolMedium
    tryExceptHandler(pool.initialize, "R", TickMath.MAX_SQRT_RATIO)
    tryExceptHandler(pool.initialize, "R", MAX_UINT160)


def test_initialize_MIN_SQRT_RATIO(createPoolMedium):
    print("can be initialized at MIN_SQRT_RATIO")
    pool, _, _, _, _ = createPoolMedium
    pool.initialize(TickMath.MIN_SQRT_RATIO)
    assert pool.slot0.tick == getMinTick(1)


def test_initialize_MAX_SQRT_RATIO_minusOne(createPoolMedium):
    print("can be initialized at MAX_SQRT_RATIO - 1")
    pool, _, _, _, _ = createPoolMedium
    pool.initialize(TickMath.MAX_SQRT_RATIO - 1)
    assert pool.slot0.tick == getMaxTick(1) - 1


def test_setInitialVariables(createPoolMedium):
    print("sets initial variables")
    pool, _, _, _, _ = createPoolMedium
    price = encodePriceSqrt(1, 2)
    pool.initialize(price)

    assert pool.slot0.sqrtPriceX96 == price
    assert pool.slot0.tick == -6932


# Mint


def test_initialize_10to1(createPoolMedium, accounts):
    pool, minTick, maxTick, _, _ = createPoolMedium
    pool.initialize(encodePriceSqrt(1, 10))
    pool.mint(accounts[0], minTick, maxTick, 3161)


def test_fails_tickLower_gtTickUpper(initializedMediumPool, accounts):
    print("fails if tickLower greater than tickUpper")
    pool, _, _, _, _ = initializedMediumPool
    tryExceptHandler(pool.mint, "TLU", accounts[0], 1, 0, 1)


def test_fails_tickLower_ltMinTick(initializedMediumPool, accounts):
    print("fails if tickLower less than min Tick")
    pool, _, _, _, _ = initializedMediumPool
    tryExceptHandler(pool.mint, "TLM", accounts[0], -887273, 0, 1)


def test_fails_tickUpper_gtMaxTick(initializedMediumPool, accounts):
    print("fails if tickUpper greater than max Tick")
    pool, _, _, _, _ = initializedMediumPool
    tryExceptHandler(pool.mint, "TUM", accounts[0], 0, 887273, 1)


def test_fails_amountGtMax(initializedMediumPool, accounts):
    print("fails if amount exceeds the max")
    pool, minTick, maxTick, _, tickSpacing = initializedMediumPool
    maxLiquidityGross = pool.maxLiquidityPerTick
    tryExceptHandler(
        pool.mint,
        "LO",
        accounts[0],
        minTick + tickSpacing,
        maxTick - tickSpacing,
        maxLiquidityGross + 1,
    )
    pool.mint(
        accounts[0], minTick + tickSpacing, maxTick - tickSpacing, maxLiquidityGross
    )


def test_fails_totalAmountatTick_gtMAX(initializedMediumPool, accounts):
    print("fails if total amount at tick exceeds the max")
    pool, minTick, maxTick, _, tickSpacing = initializedMediumPool
    pool.mint(accounts[0], minTick + tickSpacing, maxTick - tickSpacing, 1000)

    maxLiquidityGross = pool.maxLiquidityPerTick
    tryExceptHandler(
        pool.mint,
        "LO",
        accounts[0],
        minTick + tickSpacing,
        maxTick - tickSpacing,
        maxLiquidityGross - 1000 + 1,
    )
    tryExceptHandler(
        pool.mint,
        "LO",
        accounts[0],
        minTick + tickSpacing * 2,
        maxTick - tickSpacing,
        maxLiquidityGross - 1000 + 1,
    )
    tryExceptHandler(
        pool.mint,
        "LO",
        accounts[0],
        minTick + tickSpacing,
        maxTick - tickSpacing * 2,
        maxLiquidityGross - 1000 + 1,
    )
    pool.mint(
        accounts[0],
        minTick + tickSpacing,
        maxTick - tickSpacing,
        maxLiquidityGross - 1000,
    )


def test_fails_zeroAmount(initializedMediumPool, accounts):
    print("fails if amount is zero")
    pool, minTick, maxTick, _, tickSpacing = initializedMediumPool
    tryExceptHandler(
        pool.mint, "", accounts[0], minTick + tickSpacing, maxTick - tickSpacing, 0
    )


# Success cases


def test_initial_balances(initializedMediumPool):
    print("fails if amount is zero")
    pool, _, _, _, _ = initializedMediumPool
    assert pool.balances[pool.token0] == 9996
    assert pool.balances[pool.token1] == 1000


def test_initialTick(initializedMediumPool):
    print("fails if amount is zero")
    pool, _, _, _, _ = initializedMediumPool
    assert pool.slot0.tick == -23028


# Above current tick
def test_transferToken0_only(initializedMediumPool, accounts):
    print("transferToken0 only")
    pool, _, _, _, _ = initializedMediumPool
    (amount0, amount1) = pool.mint(accounts[0], -22980, 0, 10000)
    assert amount0 != 0
    assert amount1 == 0
    assert pool.balances[pool.token0] == 9996 + 21549
    assert pool.balances[pool.token1] == 1000


def test_maxTick_maxLeverage(initializedMediumPool, accounts):
    print("max tick with max leverage")
    pool, _, maxTick, _, tickSpacing = initializedMediumPool
    pool.mint(accounts[0], maxTick - tickSpacing, maxTick, 2**102)
    assert pool.balances[pool.token0] == 9996 + 828011525
    assert pool.balances[pool.token1] == 1000


def test_maxTick(initializedMediumPool, accounts):
    print("works for max tick")
    pool, _, maxTick, _, _ = initializedMediumPool
    pool.mint(accounts[0], -22980, maxTick, 10000)
    assert pool.balances[pool.token0] == 9996 + 31549
    assert pool.balances[pool.token1] == 1000


def test_remove_aboveCurrentPrice(initializedMediumPool, accounts):
    print("removing works")
    pool, _, _, _, _ = initializedMediumPool
    pool.mint(accounts[0], -240, 0, 10000)
    pool.burn(accounts[0], -240, 0, 10000)
    (_, _, _, amount0, amount1) = pool.collect(
        accounts[0], -240, 0, MAX_UINT128, MAX_UINT128
    )
    assert amount0 == 120
    assert amount1 == 0


def test_addLiquidity_toLiquidityGross(initializedMediumPool, accounts):
    print("addLiquidity to liquidity gross")
    pool, _, _, _, tickSpacing = initializedMediumPool
    pool.mint(accounts[0], -240, 0, 100)
    assert pool.ticks[-240].liquidityGross == 100
    assert pool.ticks[0].liquidityGross == 100
    # No liquidityGross === tick doesn't exist
    assert not pool.ticks.__contains__(tickSpacing)
    assert not pool.ticks.__contains__(tickSpacing * 2)
    pool.mint(accounts[0], -240, tickSpacing, 150)
    assert pool.ticks[-240].liquidityGross == 250
    assert pool.ticks[0].liquidityGross == 100
    assert pool.ticks[tickSpacing].liquidityGross == 150
    # No liquidityGross === tick doesn't exist
    assert not pool.ticks.__contains__(tickSpacing * 2)
    pool.mint(accounts[0], 0, tickSpacing * 2, 60)
    assert pool.ticks[-240].liquidityGross == 250
    assert pool.ticks[0].liquidityGross == 160
    assert pool.ticks[tickSpacing].liquidityGross == 150
    assert pool.ticks[tickSpacing * 2].liquidityGross == 60


def test_removeLiquidity_fromLiquidityGross(initializedMediumPool, accounts):
    print("removes liquidity from liquidityGross")
    pool, _, _, _, _ = initializedMediumPool
    pool.mint(accounts[0], -240, 0, 100)
    pool.mint(accounts[0], -240, 0, 40)
    pool.burn(accounts[0], -240, 0, 90)
    assert pool.ticks[-240].liquidityGross == 50
    assert pool.ticks[0].liquidityGross == 50


def test_clearTickLower_ifLastPositionRemoved(initializedMediumPool, accounts):
    print("clears tick lower if last position is removed")
    pool, _, _, _, _ = initializedMediumPool
    pool.mint(accounts[0], -240, 0, 100)
    pool.burn(accounts[0], -240, 0, 100)
    # tick cleared == not in ticks
    assert not pool.ticks.__contains__(-240)


def test_clearTickUpper_ifLastPositionRemoved(initializedMediumPool, accounts):
    print("clears tick upper if last position is removed")
    pool, _, _, _, _ = initializedMediumPool
    pool.mint(accounts[0], -240, 0, 100)
    pool.burn(accounts[0], -240, 0, 100)
    # tick cleared == not in ticks
    assert not pool.ticks.__contains__(0)


def test_clearsTick_ifNotUser(initializedMediumPool, accounts):
    print("only clears the tick that is not used at all")
    pool, _, _, _, tickSpacing = initializedMediumPool
    pool.mint(accounts[0], -240, 0, 100)
    pool.mint(accounts[1], -tickSpacing, 0, 250)
    pool.burn(accounts[0], -240, 0, 100)
    # tick cleared == not in ticks
    assert not pool.ticks.__contains__(-240)
    tickInfo = pool.ticks[-tickSpacing]
    assert tickInfo.liquidityGross == 250
    assert tickInfo.feeGrowthOutside0X128 == 0
    assert tickInfo.feeGrowthOutside1X128 == 0


# Including current price
def test_transferCurrentPriceTokens(initializedMediumPool, accounts):
    print("price within range: transfers current price of both tokens")
    pool, minTick, maxTick, _, tickSpacing = initializedMediumPool
    (amount0, amount1) = pool.mint(
        accounts[0], minTick + tickSpacing, maxTick - tickSpacing, 100
    )
    assert amount0 == 317
    assert amount1 == 32
    assert pool.balances[pool.token0] == 9996 + 317
    assert pool.balances[pool.token1] == 1000 + 32


def test_initializes_lowerTick(initializedMediumPool, accounts):
    print("initializes lower tick")
    pool, minTick, maxTick, _, tickSpacing = initializedMediumPool
    pool.mint(accounts[0], minTick + tickSpacing, maxTick - tickSpacing, 100)
    liquidityGross = pool.ticks[minTick + tickSpacing].liquidityGross
    assert liquidityGross == 100


def test_initializes_upperTick(initializedMediumPool, accounts):
    print("initializes upper tick")
    pool, minTick, maxTick, _, tickSpacing = initializedMediumPool
    pool.mint(accounts[0], minTick + tickSpacing, maxTick - tickSpacing, 100)
    liquidityGross = pool.ticks[maxTick - tickSpacing].liquidityGross
    assert liquidityGross == 100


def test_works_minMaxTick(initializedMediumPool, accounts):
    print("works for min/ max tick")
    pool, minTick, maxTick, _, _ = initializedMediumPool
    (amount0, amount1) = pool.mint(accounts[0], minTick, maxTick, 10000)
    assert amount0 == 31623
    assert amount1 == 3163
    assert pool.balances[pool.token0] == 9996 + 31623
    assert pool.balances[pool.token1] == 1000 + 3163


def test_removing_includesCurrentPrice(initializedMediumPool, accounts):
    print("removing works")
    pool, minTick, maxTick, _, tickSpacing = initializedMediumPool
    pool.mint(accounts[0], minTick + tickSpacing, maxTick - tickSpacing, 100)
    pool.burn(accounts[0], minTick + tickSpacing, maxTick - tickSpacing, 100)
    (_, _, _, amount0, amount1) = pool.collect(
        accounts[0],
        minTick + tickSpacing,
        maxTick - tickSpacing,
        MAX_UINT128,
        MAX_UINT128,
    )
    assert amount0 == 316
    assert amount1 == 31


# Below current price
def test_transfer_onlyToken1(initializedMediumPool, accounts):
    print("transfers token1 only")
    pool, _, _, _, _ = initializedMediumPool
    (amount0, amount1) = pool.mint(accounts[0], -46080, -23040, 10000)
    assert amount0 == 0
    assert amount1 == 2162
    assert pool.balances[pool.token0] == 9996
    assert pool.balances[pool.token1] == 1000 + 2162


def test_minTick_maxLeverage(initializedMediumPool, accounts):
    print("min tick with max leverage")
    pool, minTick, _, _, tickSpacing = initializedMediumPool
    pool.mint(accounts[0], minTick, minTick + tickSpacing, 2**102)
    assert pool.balances[pool.token0] == 9996
    assert pool.balances[pool.token1] == 1000 + 828011520


def test_works_minTick(initializedMediumPool, accounts):
    print("works for min tick")
    pool, minTick, _, _, _ = initializedMediumPool
    (amount0, amount1) = pool.mint(accounts[0], minTick, -23040, 10000)
    assert amount0 == 0
    assert amount1 == 3161
    assert pool.balances[pool.token0] == 9996
    assert pool.balances[pool.token1] == 1000 + 3161


def test_removing_belowCurrentPrice(initializedMediumPool, accounts):
    print("removing works")
    pool, _, _, _, _ = initializedMediumPool
    pool.mint(accounts[0], -46080, -46020, 10000)
    pool.burn(accounts[0], -46080, -46020, 10000)
    (_, _, _, amount0, amount1) = pool.collect(
        accounts[0], -46080, -46020, MAX_UINT128, MAX_UINT128
    )
    assert amount0 == 0
    assert amount1 == 3


def test_fees_duringSwap(initializedMediumPool, accounts):
    print("protocol fees accumulate as expected during swap")
    pool, minTick, maxTick, _, tickSpacing = initializedMediumPool
    pool.setFeeProtocol(6, 6)

    pool.mint(
        accounts[0], minTick + tickSpacing, maxTick - tickSpacing, expandTo18Decimals(1)
    )
    swapExact0For1(pool, expandTo18Decimals(1) // 10, accounts[0], None)
    swapExact1For0(pool, expandTo18Decimals(1) // 100, accounts[0], None)

    assert pool.protocolFees.token0 == 50000000000000
    assert pool.protocolFees.token1 == 5000000000000


def test_protectedPositions_beforefeesAreOn(initializedMediumPool, accounts):
    print("positions are protected before protocol fee is turned on")
    pool, minTick, maxTick, _, tickSpacing = initializedMediumPool
    pool.mint(
        accounts[0], minTick + tickSpacing, maxTick - tickSpacing, expandTo18Decimals(1)
    )
    swapExact0For1(pool, expandTo18Decimals(1) // 10, accounts[0], None)
    swapExact1For0(pool, expandTo18Decimals(1) // 100, accounts[0], None)

    assert pool.protocolFees.token0 == 0
    assert pool.protocolFees.token1 == 0


def test_notAllowPoke_uninitialized_position(initializedMediumPool, accounts):
    print("poke is not allowed on uninitialized position")
    pool, minTick, maxTick, _, tickSpacing = initializedMediumPool
    pool.mint(
        accounts[1], minTick + tickSpacing, maxTick - tickSpacing, expandTo18Decimals(1)
    )
    swapExact0For1(pool, expandTo18Decimals(1) // 10, accounts[0], None)
    swapExact1For0(pool, expandTo18Decimals(1) // 100, accounts[0], None)
    tryExceptHandler(
        pool.burn,
        "Position doesn't exist",
        accounts[0],
        minTick + tickSpacing,
        maxTick - tickSpacing,
        0,
    )

    pool.mint(accounts[0], minTick + tickSpacing, maxTick - tickSpacing, 1)

    position = pool.positions[
        getPositionKey(accounts[0], minTick + tickSpacing, maxTick - tickSpacing)
    ]
    assert position.liquidity == 1
    assert position.feeGrowthInside0LastX128 == 102084710076281216349243831104605583
    assert position.feeGrowthInside1LastX128 == 10208471007628121634924383110460558
    assert position.tokensOwed0 == 0, "tokens owed 0 before"
    assert position.tokensOwed1 == 0, "tokens owed 1 before"

    pool.burn(accounts[0], minTick + tickSpacing, maxTick - tickSpacing, 1)
    position = pool.positions[
        getPositionKey(accounts[0], minTick + tickSpacing, maxTick - tickSpacing)
    ]
    assert position.liquidity == 0
    assert position.feeGrowthInside0LastX128 == 102084710076281216349243831104605583
    assert position.feeGrowthInside1LastX128 == 10208471007628121634924383110460558
    assert position.tokensOwed0 == 3, "tokens owed 0 before"
    assert position.tokensOwed1 == 0, "tokens owed 1 before"


# Burn

## the combined amount of liquidity that the pool is initialized with (including the 1 minimum liquidity that is burned)
initializeLiquidityAmount = expandTo18Decimals(2)


def initializeAtZeroTick(pool, accounts):
    pool.initialize(encodePriceSqrt(1, 1))
    tickSpacing = pool.tickSpacing
    [min, max] = [getMinTick(tickSpacing), getMaxTick(tickSpacing)]
    pool.mint(accounts[0], min, max, initializeLiquidityAmount)


@pytest.fixture
def mediumPoolInitializedAtZero(createPoolMedium, accounts):
    pool, _, _, _, _ = createPoolMedium
    initializeAtZeroTick(pool, accounts)
    return createPoolMedium


def checkTickIsClear(pool, tick):
    assert pool.ticks.__contains__(tick) == False


def checkTickIsNotClear(pool, tick):
    # Make check explicit
    assert pool.ticks.__contains__(tick)
    assert pool.ticks[tick].liquidityGross != 0


def test_notClearPosition_ifNoMoreLiquidity(accounts, mediumPoolInitializedAtZero):
    pool, minTick, maxTick, _, tickSpacing = mediumPoolInitializedAtZero
    print("does not clear the position fee growth snapshot if no more liquidity")
    ## some activity that would make the ticks non-zero
    pool.mint(accounts[1], minTick, maxTick, expandTo18Decimals(1))
    swapExact0For1(pool, expandTo18Decimals(1), accounts[0], None)
    swapExact1For0(pool, expandTo18Decimals(1), accounts[0], None)
    pool.burn(accounts[1], minTick, maxTick, expandTo18Decimals(1))
    positionInfo = pool.positions[getPositionKey(accounts[1], minTick, maxTick)]
    assert positionInfo.liquidity == 0
    assert positionInfo.tokensOwed0 != 0
    assert positionInfo.tokensOwed1 != 0
    assert positionInfo.feeGrowthInside0LastX128 == 340282366920938463463374607431768211
    assert positionInfo.feeGrowthInside1LastX128 == 340282366920938463463374607431768211


def test_clearsTick_ifLastPosition(accounts, mediumPoolInitializedAtZero):
    print("clears the tick if its the last position using it")
    pool, minTick, maxTick, _, tickSpacing = mediumPoolInitializedAtZero
    tickLower = minTick + tickSpacing
    tickUpper = maxTick - tickSpacing
    ## some activity that would make the ticks non-zero
    pool.mint(accounts[0], tickLower, tickUpper, 1)
    swapExact0For1(pool, expandTo18Decimals(1), accounts[0], None)
    pool.burn(accounts[0], tickLower, tickUpper, 1)
    checkTickIsClear(pool, tickLower)
    checkTickIsClear(pool, tickUpper)


def test_clearOnlyLower_ifUpperUsed(accounts, mediumPoolInitializedAtZero):
    print("clears only the lower tick if upper is still used")
    pool, minTick, maxTick, _, tickSpacing = mediumPoolInitializedAtZero
    tickLower = minTick + tickSpacing
    tickUpper = maxTick - tickSpacing
    ## some activity that would make the ticks non-zero
    pool.mint(accounts[0], tickLower, tickUpper, 1)
    pool.mint(accounts[0], tickLower + tickSpacing, tickUpper, 1)
    swapExact0For1(pool, expandTo18Decimals(1), accounts[0], None)
    pool.burn(accounts[0], tickLower, tickUpper, 1)
    checkTickIsClear(pool, tickLower)
    checkTickIsNotClear(pool, tickUpper)


def test_clearsOnlyUpper_ifLowerUsed(accounts, mediumPoolInitializedAtZero):
    print("clears only the upper tick if lower is still used")
    pool, minTick, maxTick, _, tickSpacing = mediumPoolInitializedAtZero
    tickLower = minTick + tickSpacing
    tickUpper = maxTick - tickSpacing
    ## some activity that would make the ticks non-zero
    pool.mint(accounts[0], tickLower, tickUpper, 1)
    pool.mint(accounts[0], tickLower, tickUpper - tickSpacing, 1)
    swapExact0For1(pool, expandTo18Decimals(1), accounts[0], None)
    pool.burn(accounts[0], tickLower, tickUpper, 1)
    checkTickIsNotClear(pool, tickLower)
    checkTickIsClear(pool, tickUpper)


# Miscellaneous mint tests
@pytest.fixture
def lowPoolInitializedAtZero(createPoolLow, accounts):
    pool, _, _, _, _ = createPoolLow
    initializeAtZeroTick(pool, accounts)
    return createPoolLow


def test_mintRight_currentPrice(lowPoolInitializedAtZero, accounts):
    print("mint to the right of the current price")
    pool, _, _, _, tickSpacing = lowPoolInitializedAtZero
    liquidityDelta = 1000
    lowerTick = tickSpacing
    upperTick = tickSpacing * 2
    liquidityBefore = pool.liquidity
    b0 = pool.balances[TEST_TOKENS[0]]
    b1 = pool.balances[TEST_TOKENS[1]]

    pool.mint(accounts[0], lowerTick, upperTick, liquidityDelta)

    liquidityAfter = pool.liquidity
    assert liquidityAfter >= liquidityBefore

    assert pool.balances[TEST_TOKENS[0]] - b0 == 1
    assert pool.balances[TEST_TOKENS[1]] - b1 == 0


def test_mintLeft_currentPrice(lowPoolInitializedAtZero, accounts):
    print("mint to the right of the current price")
    pool, _, _, _, tickSpacing = lowPoolInitializedAtZero
    liquidityDelta = 1000
    lowerTick = -tickSpacing * 2
    upperTick = -tickSpacing
    liquidityBefore = pool.liquidity
    b0 = pool.balances[TEST_TOKENS[0]]
    b1 = pool.balances[TEST_TOKENS[1]]

    pool.mint(accounts[0], lowerTick, upperTick, liquidityDelta)

    liquidityAfter = pool.liquidity
    assert liquidityAfter >= liquidityBefore

    assert pool.balances[TEST_TOKENS[0]] - b0 == 0
    assert pool.balances[TEST_TOKENS[1]] - b1 == 1


def test_mint_withinCurrentPrice(lowPoolInitializedAtZero, accounts):
    print("mint within the current price")
    pool, _, _, _, tickSpacing = lowPoolInitializedAtZero
    liquidityDelta = 1000
    lowerTick = -tickSpacing
    upperTick = tickSpacing
    liquidityBefore = pool.liquidity
    b0 = pool.balances[TEST_TOKENS[0]]
    b1 = pool.balances[TEST_TOKENS[1]]

    pool.mint(accounts[0], lowerTick, upperTick, liquidityDelta)

    liquidityAfter = pool.liquidity
    assert liquidityAfter >= liquidityBefore

    assert pool.balances[TEST_TOKENS[0]] - b0 == 1
    assert pool.balances[TEST_TOKENS[1]] - b1 == 1


def test_cannotRemove_moreThanPosition(lowPoolInitializedAtZero, accounts):
    print("cannot remove more than the entire position")
    pool, _, _, _, tickSpacing = lowPoolInitializedAtZero
    lowerTick = -tickSpacing
    upperTick = tickSpacing

    pool.mint(accounts[0], lowerTick, upperTick, expandTo18Decimals(1000))

    tryExceptHandler(
        pool.burn, "LS", accounts[0], lowerTick, upperTick, expandTo18Decimals(1001)
    )


def test_collectFee_currentPrice(lowPoolInitializedAtZero, accounts, ledger):
    print("collect fees within the current price after swap")
    pool, _, _, _, tickSpacing = lowPoolInitializedAtZero
    liquidityDelta = expandTo18Decimals(100)
    lowerTick = -tickSpacing * 100
    upperTick = tickSpacing * 100

    pool.mint(accounts[0], lowerTick, upperTick, liquidityDelta)

    liquidityBefore = pool.liquidity

    amount0In = expandTo18Decimals(1)

    swapExact0For1(pool, amount0In, accounts[0], None)

    liquidityAfter = pool.liquidity

    assert liquidityAfter >= liquidityBefore, "k increases"

    token0BalanceBeforePool = pool.balances[TEST_TOKENS[0]]
    token1BalanceBeforePool = pool.balances[TEST_TOKENS[1]]
    token0BalanceBeforeWallet = ledger.balanceOf(accounts[0], TEST_TOKENS[0])
    token1BalanceBeforeWallet = ledger.balanceOf(accounts[0], TEST_TOKENS[1])

    pool.burn(accounts[0], lowerTick, upperTick, 0)
    pool.collect(accounts[0], lowerTick, upperTick, MAX_UINT128, MAX_UINT128)

    pool.burn(accounts[0], lowerTick, upperTick, 0)

    (_, _, _, amount0, amount1) = pool.collect(
        accounts[0], lowerTick, upperTick, MAX_UINT128, MAX_UINT128
    )

    assert amount0 == 0
    assert amount1 == 0

    token0BalanceAfterPool = pool.balances[TEST_TOKENS[0]]
    token1BalanceAfterPool = pool.balances[TEST_TOKENS[1]]
    token0BalanceAfterWallet = ledger.balanceOf(accounts[0], TEST_TOKENS[0])
    token1BalanceAfterWallet = ledger.balanceOf(accounts[0], TEST_TOKENS[1])

    assert token0BalanceAfterWallet > token0BalanceBeforeWallet
    assert token1BalanceAfterWallet == token1BalanceBeforeWallet
    assert token0BalanceAfterPool < token0BalanceBeforePool
    assert token1BalanceAfterPool == token1BalanceBeforePool


# pre-initialize at medium fee
def test_preInitialized_mediumFee(createPoolMedium):
    print("pre-initialized at medium fee")
    pool, _, _, _, _ = createPoolMedium
    assert pool.liquidity == 0


# post-initialize at medium fee
def test_initialLiquidity(mediumPoolInitializedAtZero):
    print("returns initial liquidity")
    pool, _, _, _, _ = mediumPoolInitializedAtZero
    assert pool.liquidity == expandTo18Decimals(2)


def test_supplyInRange(mediumPoolInitializedAtZero, accounts):
    print("returns in supply in range")
    pool, _, _, _, tickSpacing = mediumPoolInitializedAtZero
    pool.mint(accounts[0], -tickSpacing, tickSpacing, expandTo18Decimals(3))
    assert pool.liquidity == expandTo18Decimals(5)


def test_excludeSupply_tickAboveCurrentTick(mediumPoolInitializedAtZero, accounts):
    print("excludes supply at tick above current tick")
    pool, _, _, _, tickSpacing = mediumPoolInitializedAtZero
    pool.mint(accounts[0], tickSpacing, tickSpacing * 2, expandTo18Decimals(3))
    assert pool.liquidity == expandTo18Decimals(2)


def test_excludeSupply_tickBelowCurrentTick(mediumPoolInitializedAtZero, accounts):
    print("excludes supply at tick below current tick")
    pool, _, _, _, tickSpacing = mediumPoolInitializedAtZero
    pool.mint(accounts[0], -tickSpacing * 2, -tickSpacing, expandTo18Decimals(3))
    assert pool.liquidity == expandTo18Decimals(2)


def test_updatesWhenExitingRange(mediumPoolInitializedAtZero, accounts):
    print("updates correctly when exiting range")
    pool, _, _, _, tickSpacing = mediumPoolInitializedAtZero

    kBefore = pool.liquidity
    assert kBefore == expandTo18Decimals(2)

    ## add liquidity at and above current tick
    liquidityDelta = expandTo18Decimals(1)
    lowerTick = 0
    upperTick = tickSpacing
    pool.mint(accounts[0], lowerTick, upperTick, liquidityDelta)

    ## ensure virtual supply has increased appropriately
    kAfter = pool.liquidity
    assert kAfter == expandTo18Decimals(3)

    ## swap toward the left (just enough for the tick transition function to trigger)
    swapExact0For1(pool, 1, accounts[0], None)
    assert pool.slot0.tick == -1

    kAfterSwap = pool.liquidity
    assert kAfterSwap == expandTo18Decimals(2)


def test_updatesWhenEnteringRange(mediumPoolInitializedAtZero, accounts):
    print("updates correctly when entering range")
    pool, _, _, _, tickSpacing = mediumPoolInitializedAtZero

    kBefore = pool.liquidity
    assert kBefore == expandTo18Decimals(2)

    ## add liquidity at and below current tick
    liquidityDelta = expandTo18Decimals(1)
    lowerTick = -tickSpacing
    upperTick = 0
    pool.mint(accounts[0], lowerTick, upperTick, liquidityDelta)

    ## ensure virtual supply has increased appropriately
    kAfter = pool.liquidity
    assert kAfter == kBefore
    ## swap toward the right (just enough for the tick transition function to trigger)
    swapExact0For1(pool, 1, accounts[0], None)
    assert pool.slot0.tick == -1

    kAfterSwap = pool.liquidity
    assert kAfterSwap == expandTo18Decimals(3)


# Limit orders


def test_limitSelling0For1_atTick0Thru1(mediumPoolInitializedAtZero, accounts):
    print("limit selling 0 for 1 at tick 0 thru 1")
    pool, _, _, _, _ = mediumPoolInitializedAtZero

    (amount0, amount1) = pool.mint(accounts[0], 0, 120, expandTo18Decimals(1))
    assert amount0 == 5981737760509663
    assert amount1 == 0

    ## somebody takes the limit order
    swapExact1For0(pool, expandTo18Decimals(2), accounts[0], None)
    (recipient, tickLower, tickUpper, amount, amount0, amount1) = pool.burn(
        accounts[0], 0, 120, expandTo18Decimals(1)
    )
    assert (recipient, tickLower, tickUpper, amount, amount0, amount1) == (
        accounts[0],
        0,
        120,
        expandTo18Decimals(1),
        0,
        6017734268818165,
    )

    (recipient, _, _, amount0, amount1) = pool.collect(
        accounts[0], 0, 120, MAX_UINT128, MAX_UINT128
    )

    assert amount0 == 0
    assert amount1 == 6017734268818165 + 18107525382602
    assert recipient == accounts[0]

    assert pool.slot0.tick >= 120


# Fee is ON
def test_limitSelling0For1_atTick0Thru1_feesOn(mediumPoolInitializedAtZero, accounts):
    print("limit selling 0 for 1 at tick 0 thru 1 - fees on")
    pool, _, _, _, _ = mediumPoolInitializedAtZero
    pool.setFeeProtocol(6, 6)

    (amount0, amount1) = pool.mint(accounts[0], 0, 120, expandTo18Decimals(1))
    assert amount0 == 5981737760509663
    assert amount1 == 0

    ## somebody takes the limit order
    swapExact1For0(pool, expandTo18Decimals(2), accounts[0], None)

    (recipient, tickLower, tickUpper, amount, amount0, amount1) = pool.burn(
        accounts[0], 0, 120, expandTo18Decimals(1)
    )
    assert recipient == accounts[0]
    assert tickLower == 0
    assert tickUpper == 120
    assert amount == expandTo18Decimals(1)
    assert amount0 == 0
    assert amount1 == 6017734268818165

    (recipient, _, _, amount0, amount1) = pool.collect(
        accounts[0], 0, 120, MAX_UINT128, MAX_UINT128
    )
    assert recipient == accounts[0]
    assert amount0 == 0
    assert (
        amount1 == 6017734268818165 + 15089604485501
    )  ## roughly 0.25% despite other liquidity

    assert pool.slot0.tick >= 120


def test_limitSelling0For1_atTick0ThruMinus1_feesOn(
    mediumPoolInitializedAtZero, accounts
):
    print("limit selling 0 for 1 at tick 0 thru -1 - fees on")
    pool, _, _, _, _ = mediumPoolInitializedAtZero
    pool.setFeeProtocol(6, 6)

    (amount0, amount1) = pool.mint(accounts[0], -120, 0, expandTo18Decimals(1))
    assert amount0 == 0
    assert amount1 == 5981737760509663

    ## somebody takes the limit order
    swapExact0For1(pool, expandTo18Decimals(2), accounts[0], None)

    (recipient, tickLower, tickUpper, amount, amount0, amount1) = pool.burn(
        accounts[0], -120, 0, expandTo18Decimals(1)
    )
    assert recipient == accounts[0]
    assert tickLower == -120
    assert tickUpper == 0
    assert amount == expandTo18Decimals(1)
    assert amount0 == 6017734268818165
    assert amount1 == 0

    (recipient, _, _, amount0, amount1) = pool.collect(
        accounts[0], -120, 0, MAX_UINT128, MAX_UINT128
    )
    assert recipient == accounts[0]
    assert (
        amount0 == 6017734268818165 + 15089604485501
    )  ## roughly 0.25% despite other liquidity
    assert amount1 == 0

    assert pool.slot0.tick <= -120


## Collect
def test_multipleLPs(initializedLowPoolCollect, accounts):
    print("works with multiple LPs")
    pool, minTick, maxTick, _, tickSpacing = initializedLowPoolCollect
    pool.mint(accounts[0], minTick, maxTick, expandTo18Decimals(1))
    pool.mint(
        accounts[0], minTick + tickSpacing, maxTick - tickSpacing, expandTo18Decimals(2)
    )

    swapExact0For1(pool, expandTo18Decimals(1), accounts[0], None)

    ## poke positions
    pool.burn(accounts[0], minTick, maxTick, 0)

    pool.burn(accounts[0], minTick + tickSpacing, maxTick - tickSpacing, 0)

    position0 = pool.positions[getPositionKey(accounts[0], minTick, maxTick)]
    position1 = pool.positions[
        getPositionKey(accounts[0], minTick + tickSpacing, maxTick - tickSpacing)
    ]

    assert position0.tokensOwed0 == 166666666666666
    assert position1.tokensOwed0 == 333333333333333


## Works accross large increases

## type(uint128).max * 2**128 / 1e18
## https://www.wolframalpha.com/input/?i=%282**128+-+1%29+*+2**128+%2F+1e18
magicNumber = 115792089237316195423570985008687907852929702298719625575994


def test_justBeforeCapBinds(initializedLowPoolCollect, accounts):
    print("works just before the cap binds")
    pool, minTick, maxTick, _, _ = initializedLowPoolCollect
    pool.mint(accounts[0], minTick, maxTick, expandTo18Decimals(1))

    pool.feeGrowthGlobal0X128 = magicNumber
    pool.burn(accounts[0], minTick, maxTick, 0)
    positionInfo = pool.positions[getPositionKey(accounts[0], minTick, maxTick)]
    assert positionInfo.tokensOwed0 == MAX_UINT128 - 1
    assert positionInfo.tokensOwed1 == 0


def test_justAfterCapBinds(initializedLowPoolCollect, accounts):
    print("works just after the cap binds")
    pool, minTick, maxTick, _, _ = initializedLowPoolCollect
    pool.mint(accounts[0], minTick, maxTick, expandTo18Decimals(1))

    pool.feeGrowthGlobal0X128 = magicNumber + 1
    pool.burn(accounts[0], minTick, maxTick, 0)

    positionInfo = pool.positions[getPositionKey(accounts[0], minTick, maxTick)]

    assert positionInfo.tokensOwed0 == MAX_UINT128
    assert positionInfo.tokensOwed1 == 0


# Causes overflow on the position.update() for tokensOwed0. In Uniswap the overflow is
# acceptable because it is expected for the LP to collect the tokens before it happens.
def test_afterCapBinds(initializedLowPoolCollect, accounts):
    print("works after the cap binds")
    pool, minTick, maxTick, _, _ = initializedLowPoolCollect
    pool.mint(accounts[0], minTick, maxTick, expandTo18Decimals(1))

    pool.feeGrowthGlobal0X128 = MAX_UINT256

    # Overflown tokensOwed0 - added code to Position.py to handle this
    pool.burn(accounts[0], minTick, maxTick, 0)

    positionInfo = pool.positions[getPositionKey(accounts[0], minTick, maxTick)]

    assert positionInfo.tokensOwed0 == MAX_UINT128
    assert positionInfo.tokensOwed1 == 0


# Works across overflow boundaries
@pytest.fixture
def initializedLowPoolCollectGrowthFees(initializedLowPoolCollect, accounts):
    pool, minTick, maxTick, _, _ = initializedLowPoolCollect
    pool.feeGrowthGlobal0X128 = MAX_UINT256
    pool.feeGrowthGlobal1X128 = MAX_UINT256
    pool.mint(accounts[0], minTick, maxTick, expandTo18Decimals(10))
    return initializedLowPoolCollect


def test_token0(initializedLowPoolCollectGrowthFees, accounts):
    print("token0")
    pool, minTick, maxTick, _, _ = initializedLowPoolCollectGrowthFees

    swapExact0For1(pool, expandTo18Decimals(1), accounts[0], None)
    pool.burn(accounts[0], minTick, maxTick, 0)
    (_, _, _, amount0, amount1) = pool.collect(
        accounts[0], minTick, maxTick, MAX_UINT128, MAX_UINT128
    )
    assert amount0 == 499999999999999
    assert amount1 == 0


def test_token1(initializedLowPoolCollectGrowthFees, accounts):
    print("token1")
    pool, minTick, maxTick, _, _ = initializedLowPoolCollectGrowthFees

    swapExact1For0(pool, expandTo18Decimals(1), accounts[0], None)
    pool.burn(accounts[0], minTick, maxTick, 0)
    (_, _, _, amount0, amount1) = pool.collect(
        accounts[0], minTick, maxTick, MAX_UINT128, MAX_UINT128
    )
    assert amount0 == 0
    assert amount1 == 499999999999999


def test_token0_and_token1(initializedLowPoolCollectGrowthFees, accounts):
    print("token0 and token1")
    pool, minTick, maxTick, _, _ = initializedLowPoolCollectGrowthFees

    swapExact0For1(pool, expandTo18Decimals(1), accounts[0], None)
    swapExact1For0(pool, expandTo18Decimals(1), accounts[0], None)
    pool.burn(accounts[0], minTick, maxTick, 0)
    (_, _, _, amount0, amount1) = pool.collect(
        accounts[0], minTick, maxTick, MAX_UINT128, MAX_UINT128
    )
    assert amount0 == 499999999999999
    assert amount1 == 499999999999999


# Fee Protocol
liquidityAmount = expandTo18Decimals(1000)


@pytest.fixture
def initializedLowPoolCollectFees(initializedLowPoolCollect, accounts):
    pool, minTick, maxTick, _, _ = initializedLowPoolCollect
    pool.mint(accounts[0], minTick, maxTick, liquidityAmount)
    return initializedLowPoolCollect


def test_initiallyZero(initializedLowPoolCollectFees):
    print("is initially set to 0")
    pool, _, _, _, _ = initializedLowPoolCollectFees

    assert pool.slot0.feeProtocol == 0


def test_changeProtocolFee(initializedLowPoolCollectFees):
    print("can be changed")
    pool, _, _, _, _ = initializedLowPoolCollectFees

    pool.setFeeProtocol(6, 6)
    assert pool.slot0.feeProtocol == 102


def test_cannotOutOfBounds(initializedLowPoolCollectFees):
    pool, _, _, _, _ = initializedLowPoolCollectFees
    tryExceptHandler(pool.setFeeProtocol, "", 3, 3)
    tryExceptHandler(pool.setFeeProtocol, "", 11, 11)


def swapAndGetFeesOwed(createPoolParams, amount, zeroForOne, poke, account):
    pool, minTick, maxTick, _, _ = createPoolParams
    if zeroForOne:
        swapExact0For1(pool, amount, account, None)
    else:
        swapExact1For0(pool, amount, account, None)

    if poke:
        pool.burn(account, minTick, maxTick, 0)

    # Copy pool instance to check that the accrued fees are correct but allowing to accumulate
    (_, _, _, fees0, fees1) = copy.deepcopy(pool).collect(
        account, minTick, maxTick, MAX_UINT128, MAX_UINT128
    )

    assert fees0 >= 0, "fees owed in token0 are greater than 0"
    assert fees1 >= 0, "fees owed in token1 are greater than 0"

    return (fees0, fees1)


def test_positionOwner_fullFees_feeProtocolOff(initializedLowPoolCollectFees, accounts):
    print("position owner gets full fees when protocol fee is off")
    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), True, True, accounts[0]
    )
    ## 6 bips * 1e18
    assert token0Fees == 499999999999999
    assert token1Fees == 0


def test_swapFeesAccomulate_zeroForOne(initializedLowPoolCollectFees, accounts):
    print("swap fees accumulate as expected (0 for 1)")

    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), True, True, accounts[0]
    )
    assert token0Fees == 499999999999999
    assert token1Fees == 0

    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), True, True, accounts[0]
    )
    assert token0Fees == 999999999999998
    assert token1Fees == 0

    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), True, True, accounts[0]
    )
    assert token0Fees == 1499999999999997
    assert token1Fees == 0


# check that swapping 1e18 twice adds to almost the same exact fees as swapping 2e18 once
def test_swapFeesAccomulate_zeroForOne_together0(
    initializedLowPoolCollectFees, accounts
):
    print("swap fees accumulate as expected (0 for 1)")

    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(2), True, True, accounts[0]
    )
    assert token0Fees == 999999999999999
    assert token1Fees == 0


# check that swapping 1e18 multiple times adds to almost the same exact fees as swapping once
def test_swapFeesAccomulate_zeroForOne_together1(
    initializedLowPoolCollectFees, accounts
):
    print("swap fees accumulate as expected (0 for 1)")

    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(3), True, True, accounts[0]
    )
    assert token0Fees == 1499999999999999
    assert token1Fees == 0


def test_swapFeesAccomulate_OneForZero(initializedLowPoolCollectFees, accounts):
    print("swap fees accumulate as expected (1 for 0)")

    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), False, True, accounts[0]
    )

    assert token0Fees == 0
    assert token1Fees == 499999999999999

    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), False, True, accounts[0]
    )
    assert token0Fees == 0
    assert token1Fees == 999999999999998

    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), False, True, accounts[0]
    )
    assert token0Fees == 0
    assert token1Fees == 1499999999999997


# check that swapping 1e18 multiple times adds to almost the same exact fees as swapping once
def test_swapFeesAccomulate_OneForZero_together0(
    initializedLowPoolCollectFees, accounts
):
    print("swap fees accumulate as expected (1 for 0)")

    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(2), False, True, accounts[0]
    )

    assert token0Fees == 0
    assert token1Fees == 999999999999999


def test_swapFeesAccomulate_OneForZero_together1(
    initializedLowPoolCollectFees, accounts
):
    print("swap fees accumulate as expected (1 for 0)")

    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(3), False, True, accounts[0]
    )

    assert token0Fees == 0
    assert token1Fees == 1499999999999999


def test_partialFees_feeProtocolOn(initializedLowPoolCollectFees, accounts):
    print("position owner gets partial fees when protocol fee is on")
    pool, _, _, _, _ = initializedLowPoolCollectFees

    pool.setFeeProtocol(6, 6)
    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), True, True, accounts[0]
    )
    assert token0Fees == 416666666666666
    assert token1Fees == 0


# Collect protocol


def test_returnsZero_noFees(initializedLowPoolCollectFees, accounts):
    print("returns 0 if no fees")
    pool, _, _, _, _ = initializedLowPoolCollectFees
    pool.setFeeProtocol(6, 6)

    (_, amount0, amount1) = pool.collectProtocol(accounts[0], MAX_UINT128, MAX_UINT128)
    assert amount0 == 0
    assert amount1 == 0


def test_canCollectFees(initializedLowPoolCollectFees, accounts):
    print("can collect fees")
    pool, _, _, _, _ = initializedLowPoolCollectFees
    pool.setFeeProtocol(6, 6)

    swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), True, True, accounts[0]
    )

    (_, amount0, amount1) = pool.collectProtocol(accounts[0], MAX_UINT128, MAX_UINT128)
    assert amount0 == 83333333333332
    assert amount1 == 0


def test_feesDifferToken0Token1(initializedLowPoolCollectFees, accounts):
    print("fees collected can differ between token0 and token1")
    pool, _, _, _, _ = initializedLowPoolCollectFees
    pool.setFeeProtocol(8, 5)

    swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), True, False, accounts[0]
    )

    swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), False, False, accounts[0]
    )

    (_, amount0, amount1) = pool.collectProtocol(accounts[0], MAX_UINT128, MAX_UINT128)
    ## more token0 fees because it's 1/5th the swap fees
    assert amount0 == 62499999999999
    ## less token1 fees because it's 1/8th the swap fees
    assert amount1 == 99999999999999


def test_doubleFees(initializedLowPoolCollectFees, accounts):
    print("fees collected by lp after two swaps should be double one swap")

    pool, _, _, _, _ = initializedLowPoolCollectFees

    swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), True, True, accounts[0]
    )

    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), True, True, accounts[0]
    )

    ## 6 bips * 2e18
    assert token0Fees == 999999999999998
    assert token1Fees == 0


def test_feesCollected_combination0(initializedLowPoolCollectFees, accounts):
    print(
        "fees collected after two swaps with fee turned on in middle are fees from last swap (not confiscatory)"
    )
    pool, _, _, _, _ = initializedLowPoolCollectFees

    swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), True, False, accounts[0]
    )
    pool.setFeeProtocol(6, 6)
    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), True, True, accounts[0]
    )
    assert token0Fees == 916666666666666
    assert token1Fees == 0


def test_feesCollected_combination1(initializedLowPoolCollectFees, accounts):
    print("fees collected by lp after two swaps with intermediate withdrawal")
    pool, minTick, maxTick, _, _ = initializedLowPoolCollectFees
    pool.setFeeProtocol(6, 6)

    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), True, True, accounts[0]
    )
    assert token0Fees == 416666666666666
    assert token1Fees == 0

    pool.collect(accounts[0], minTick, maxTick, MAX_UINT128, MAX_UINT128)

    (token0Fees, token1Fees) = swapAndGetFeesOwed(
        initializedLowPoolCollectFees, expandTo18Decimals(1), True, False, accounts[0]
    )
    assert token0Fees == 0
    assert token1Fees == 0

    assert pool.protocolFees.token0 == 166666666666666
    assert pool.protocolFees.token1 == 0

    pool.burn(accounts[0], minTick, maxTick, 0)  ## poke to update fees

    (recipient, _, _, amount0, amount1) = pool.collect(
        accounts[0], minTick, maxTick, MAX_UINT128, MAX_UINT128
    )
    assert (recipient, amount0, amount1) == (accounts[0], 416666666666666, 0)

    assert pool.protocolFees.token0 == 166666666666666
    assert pool.protocolFees.token1 == 0


@pytest.fixture
def createPoolMedium12TickSpacing(TEST_POOLS, ledger):
    return createPool(TEST_POOLS, FeeAmount.MEDIUM, 12, ledger)


@pytest.fixture
def initializedPoolMedium12TickSpacing(createPoolMedium12TickSpacing):
    pool, _, _, _, _ = createPoolMedium12TickSpacing
    pool.initialize(encodePriceSqrt(1, 1))
    return createPoolMedium12TickSpacing


def test_mint_onlyMultiplesOf12(initializedPoolMedium12TickSpacing, accounts):
    print("mint can only be called for multiples of 12")
    pool, _, _, _, _ = initializedPoolMedium12TickSpacing
    tryExceptHandler(pool.mint, "", accounts[0], -6, 0, 1)
    tryExceptHandler(pool.mint, "", accounts[0], 0, 6, 1)


def test_mint_multiplesOf12(initializedPoolMedium12TickSpacing, accounts):
    print("mint can be called for multiples of 12")
    pool, _, _, _, _ = initializedPoolMedium12TickSpacing
    pool.mint(accounts[0], 12, 24, 1)
    pool.mint(accounts[0], -144, -120, 1)


def test_swapGaps_oneForZero(initializedPoolMedium12TickSpacing, accounts):
    print("swapping across gaps works in 1 for 0 direction")
    pool, _, _, _, _ = initializedPoolMedium12TickSpacing
    liquidityAmount = expandTo18Decimals(1) // 4
    amount0, amount1 = pool.mint(accounts[0], 120000, 121200, liquidityAmount)
    swapExact1For0(pool, expandTo18Decimals(1), accounts[0], None)
    (recipient, tickLower, tickUpper, amount, amount0, amount1) = pool.burn(
        accounts[0], 120000, 121200, liquidityAmount
    )
    assert (recipient, tickLower, tickUpper, amount, amount0, amount1) == (
        accounts[0],
        120000,
        121200,
        liquidityAmount,
        30027458295511,
        996999999999999999,
    )
    assert pool.slot0.tick == 120196


def test_swapGaps_zeroForOne(initializedPoolMedium12TickSpacing, accounts):
    print("swapping across gaps works in 0 for 1 direction")
    pool, _, _, _, _ = initializedPoolMedium12TickSpacing
    liquidityAmount = expandTo18Decimals(1) // 4
    pool.mint(accounts[0], -121200, -120000, liquidityAmount)
    swapExact0For1(pool, expandTo18Decimals(1), accounts[0], None)
    (recipient, tickLower, tickUpper, amount, amount0, amount1) = pool.burn(
        accounts[0], -121200, -120000, liquidityAmount
    )
    assert (recipient, tickLower, tickUpper, amount, amount0, amount1) == (
        accounts[0],
        -121200,
        -120000,
        liquidityAmount,
        996999999999999999,
        30027458295511,
    )
    assert pool.slot0.tick == -120197


## https://github.com/Uniswap/uniswap-v3-core/issues/214
def test_noTickTransitionTwice(TEST_POOLS, accounts, ledger):
    print(
        "tick transition cannot run twice if zero for one swap ends at fractional price just below tick"
    )
    pool, _, _, _, _ = createPool(TEST_POOLS, FeeAmount.MEDIUM, 1, ledger)

    p0 = TickMath.getSqrtRatioAtTick(-24081) + 1
    ## initialize at a price of ~0.3 token1/token0
    ## meaning if you swap in 2 token0, you should end up getting 0 token1
    pool.initialize(p0)
    assert pool.liquidity == 0, "current pool liquidity is 1"
    assert pool.slot0.tick == -24081, "pool tick is -24081"

    ## add a bunch of liquidity around current price
    liquidity = expandTo18Decimals(1000)
    pool.mint(accounts[0], -24082, -24080, liquidity)
    assert pool.liquidity == liquidity, "current pool liquidity is now liquidity + 1"

    pool.mint(accounts[0], -24082, -24081, liquidity)
    assert pool.liquidity == liquidity, "current pool liquidity is still liquidity + 1"

    ## check the math works out to moving the price down 1, sending no amount out, and having some amount remaining
    (sqrtQ, amountIn, amountOut, feeAmount) = SwapMath.computeSwapStep(
        p0, p0 - 1, liquidity, 3, FeeAmount.MEDIUM
    )
    assert sqrtQ == p0 - 1, "price moves"
    assert feeAmount == 1, "fee amount is 1"
    assert amountIn == 1, "amount in is 1"
    assert amountOut == 0, "zero amount out"


# setFeeProtocol
@pytest.fixture
def initializedSetFeeProtPool(createPoolMedium):
    pool, _, _, _, _ = createPoolMedium
    pool.initialize(encodePriceSqrt(1, 1))
    return createPoolMedium


def test_failsFeeLt4OrGt10(initializedSetFeeProtPool, accounts):
    print("fails if fee is lt 4 or gt 10")
    pool, _, _, _, _ = initializedSetFeeProtPool
    tryExceptHandler(pool.setFeeProtocol, "", 3, 3)
    tryExceptHandler(pool.setFeeProtocol, "", 6, 3)
    tryExceptHandler(pool.setFeeProtocol, "", 3, 6)
    tryExceptHandler(pool.setFeeProtocol, "", 11, 11)
    tryExceptHandler(pool.setFeeProtocol, "", 6, 11)
    tryExceptHandler(pool.setFeeProtocol, "", 11, 6)


def test_setFeeProtocol_4(initializedSetFeeProtPool):
    print("succeeds for fee of 4")
    pool, _, _, _, _ = initializedSetFeeProtPool
    pool.setFeeProtocol(4, 4)


def test_setFeeProtocol_10(initializedSetFeeProtPool):
    print("succeeds for fee of 10")
    pool, _, _, _, _ = initializedSetFeeProtPool
    pool.setFeeProtocol(10, 10)


def test_setFeeProtocol_7(initializedSetFeeProtPool):
    print("succeeds for fee of 7")
    pool, _, _, _, _ = initializedSetFeeProtPool
    pool.setFeeProtocol(7, 7)
    assert pool.slot0.feeProtocol == 119


def test_changeProtocolFee(initializedSetFeeProtPool):
    print("can change protocol fee")
    pool, _, _, _, _ = initializedSetFeeProtPool
    pool.setFeeProtocol(7, 7)
    pool.setFeeProtocol(5, 8)
    assert pool.slot0.feeProtocol == 133


def test_turnOffProtocolFee(initializedSetFeeProtPool):
    print("can turn off protocol fee")
    pool, _, _, _, _ = initializedSetFeeProtPool
    pool.setFeeProtocol(4, 4)
    pool.setFeeProtocol(0, 0)
    assert pool.slot0.feeProtocol == 0


def test_turnOnProtocolFee_returns(initializedSetFeeProtPool):
    print("returns when turned on")
    pool, _, _, _, _ = initializedSetFeeProtPool
    feeProtocolOld0, feeProtocolOld1, feeProtocol0, feeProtocol1 = pool.setFeeProtocol(
        7, 7
    )
    assert feeProtocolOld0 == 0
    assert feeProtocolOld1 == 0
    assert feeProtocol0 == 7
    assert feeProtocol1 == 7


def test_turnOffProtocolFee_returns(initializedSetFeeProtPool):
    print("returns when turned off")
    pool, _, _, _, _ = initializedSetFeeProtPool
    pool.setFeeProtocol(7, 5)
    feeProtocolOld0, feeProtocolOld1, feeProtocol0, feeProtocol1 = pool.setFeeProtocol(
        0, 0
    )
    assert feeProtocolOld0 == 7
    assert feeProtocolOld1 == 5
    assert feeProtocol0 == 0
    assert feeProtocol1 == 0


def test_changeProtocolFee_returns(initializedSetFeeProtPool):
    print("returns when changed")
    pool, _, _, _, _ = initializedSetFeeProtPool
    pool.setFeeProtocol(4, 10)
    feeProtocolOld0, feeProtocolOld1, feeProtocol0, feeProtocol1 = pool.setFeeProtocol(
        6, 8
    )
    assert feeProtocolOld0 == 4
    assert feeProtocolOld1 == 10
    assert feeProtocol0 == 6
    assert feeProtocol1 == 8


def test_unchangedProtocolFee_returns(initializedSetFeeProtPool):
    print("returns when unchanged")
    pool, _, _, _, _ = initializedSetFeeProtPool
    pool.setFeeProtocol(5, 9)
    feeProtocolOld0, feeProtocolOld1, feeProtocol0, feeProtocol1 = pool.setFeeProtocol(
        5, 9
    )
    assert feeProtocolOld0 == 5
    assert feeProtocolOld1 == 9
    assert feeProtocol0 == 5
    assert feeProtocol1 == 9


@pytest.fixture
def initializedPoolSwapBalances(initializedSetFeeProtPool, accounts):
    pool, minTick, maxTick, _, _ = initializedSetFeeProtPool
    pool.mint(accounts[0], minTick, maxTick, expandTo18Decimals(1))
    return initializedSetFeeProtPool


def test_enoughBalance_token0(initializedPoolSwapBalances, accounts, ledger):
    print("swapper swaps all token0")
    pool, _, _, _, _ = initializedPoolSwapBalances

    # Set the balance of the account to < MAX_INT128
    ledger.accounts[accounts[2]].balances[TEST_TOKENS[0]] = expandTo18Decimals(1)

    swapExact0For1(
        pool, ledger.balanceOf(accounts[2], TEST_TOKENS[0]), accounts[2], None
    )
    assert ledger.balanceOf(accounts[2], TEST_TOKENS[0]) == 0


def test_enoughBalance_token1(initializedPoolSwapBalances, accounts, ledger):
    print("swapper doesn't have enough token0")
    pool, _, _, _, _ = initializedPoolSwapBalances

    # Set the balance of the account to < MAX_INT128
    ledger.accounts[accounts[2]].balances[TEST_TOKENS[1]] = expandTo18Decimals(1)

    swapExact1For0(
        pool, ledger.balanceOf(accounts[2], TEST_TOKENS[1]), accounts[2], None
    )
    assert ledger.balanceOf(accounts[2], TEST_TOKENS[1]) == 0


def test_notEnoughBalance_token0(initializedPoolSwapBalances, accounts, ledger):
    print("swapper doesn't have enough token0")
    pool, _, _, _, _ = initializedPoolSwapBalances

    # Set the balance of the account to < MAX_INT128
    ledger.accounts[accounts[2]].balances[TEST_TOKENS[0]] = expandTo18Decimals(1)
    initialBalanceToken0 = ledger.balanceOf(accounts[2], TEST_TOKENS[0])

    tryExceptHandler(
        swapExact0For1,
        "Insufficient balance",
        pool,
        ledger.balanceOf(accounts[2], TEST_TOKENS[0]) + 1,
        accounts[2],
        None,
    )
    assert ledger.balanceOf(accounts[2], TEST_TOKENS[0]) == initialBalanceToken0


def test_notEnoughBalance_token1(initializedPoolSwapBalances, accounts, ledger):
    print("swapper doesn't have enough token1")
    pool, _, _, _, _ = initializedPoolSwapBalances

    # Set the balance of the account to < MAX_INT128
    ledger.accounts[accounts[2]].balances[TEST_TOKENS[1]] = expandTo18Decimals(1)
    initialBalanceToken1 = ledger.balanceOf(accounts[2], TEST_TOKENS[1])

    tryExceptHandler(
        swapExact1For0,
        "Insufficient balance",
        pool,
        ledger.balanceOf(accounts[2], TEST_TOKENS[1]) + 1,
        accounts[2],
        None,
    )
    assert ledger.balanceOf(accounts[2], TEST_TOKENS[1]) == initialBalanceToken1


# Extra tests since there are modifications in the python UniswapPool. Due to the difference
# in mappings between the python and the solidity we have added an assertion when positions
# don't exist (to not create it).
def test_fails_collectEmpty(createPoolMedium, accounts):
    print("Cannot collect a non-existent position")
    pool, minTick, maxTick, _, _ = createPoolMedium
    tryExceptHandler(
        pool.collect, "Position doesn't exist", accounts[0], minTick, maxTick, 0, 0
    )
    tryExceptHandler(
        pool.collect, "Position doesn't exist", accounts[0], minTick, maxTick, 1, 1
    )
    tryExceptHandler(pool.collect, "Position doesn't exist", accounts[0], 0, 0, 0, 0)


def test_collectEmpty_noPositionCreated_emptyPool(createPoolMedium, accounts):
    print(
        "Check that new positions are not created (reverts) when we collect an empty position"
    )
    pool, minTick, maxTick, _, _ = createPoolMedium
    assert pool.ticks == {}
    tryExceptHandler(
        pool.collect, "Position doesn't exist", accounts[0], minTick, maxTick, 0, 0
    )
    # Check that no position has been created
    assert pool.ticks == {}


def test_collectEmpty_noPositionCreated_initializedPool(
    mediumPoolInitializedAtZero, accounts
):
    print(
        "Check that new positions are not created (reverts) when we collect an empty position"
    )
    pool, minTick, maxTick, _, _ = mediumPoolInitializedAtZero
    initialTicks = copy.deepcopy(pool.ticks)
    tryExceptHandler(
        pool.collect, "Position doesn't exist", accounts[1], minTick, maxTick, 0, 0
    )
    # Check that no position has been created
    assert initialTicks == pool.ticks


# Not allow burning >0 in a non-existent position
def test_burnGtZero_noPositionCreated_initializedPool(createPoolMedium, accounts):
    print(
        "test that burn > 0 a non-existent position doesn't create a new position(reverts)"
    )
    pool, minTick, maxTick, _, _ = createPoolMedium
    initialTicks = pool.ticks
    tryExceptHandler(
        pool.burn, "Position doesn't exist", accounts[1], minTick, maxTick, 1
    )
    assert initialTicks == pool.ticks


# Allow burning zero in an existing position (poke) but make sure no new position is created if
# burn zero is done on a non-existent position
def test_burnZero_noPositionCreated_initializedPool(createPoolMedium, accounts):
    print(
        "test that burn zero (== poke) a non-existent position doesn't create a new position(reverts)"
    )
    pool, minTick, maxTick, _, _ = createPoolMedium
    initialTicks = pool.ticks
    tryExceptHandler(
        pool.burn,
        "Position doesn't exist",
        accounts[1],
        minTick,
        maxTick,
        0,
    )
    assert initialTicks == pool.ticks
