from .utilities import *
from .poolFixtures import *
from .test_uniswapPool import accounts, ledger
from .UniswapV3PoolSwaps import swapsSnapshot

from ..src.UniswapPool import *
from ..src.libraries.Factory import *


@pytest.fixture(params=[*range(0, 15, 1)])
def TEST_POOLS(request, accounts, ledger):
    poolFixture = request.getfixturevalue("pool{}".format(request.param))
    feeAmount = poolFixture.feeAmount
    tickSpacing = poolFixture.tickSpacing
    pool = UniswapPool(TEST_TOKENS[0], TEST_TOKENS[1], feeAmount, tickSpacing, ledger)
    pool.initialize(poolFixture.startingPrice)
    for position in poolFixture.positions:
        pool.mint(
            accounts[0], position.tickLower, position.tickUpper, position.liquidity
        )
    poolBalance0 = pool.balances[TEST_TOKENS[0]]
    poolBalance1 = pool.balances[TEST_TOKENS[1]]
    return (
        TEST_TOKENS[0],
        TEST_TOKENS[1],
        pool,
        poolBalance0,
        poolBalance1,
        accounts[1],
        poolFixture,
    )


@pytest.fixture
def afterEach(accounts, TEST_POOLS):
    yield
    print("check can burn positions")
    (_, _, pool, _, _, _, poolFixture) = TEST_POOLS
    for position in poolFixture.positions:
        pool.burn(
            accounts[0], position.tickLower, position.tickUpper, position.liquidity
        )
        pool.collect(
            accounts[0],
            position.tickLower,
            position.tickUpper,
            MAX_UINT128,
            MAX_UINT128,
        )


# UniswapV3Pool swap tests


@pytest.mark.usefixtures("afterEach")
def test_uniswap_swaps(TEST_POOLS):
    (_, _, pool, poolBalance0, poolBalance1, recipient, poolFixture) = TEST_POOLS
    print(poolFixture.description)

    if poolFixture.swapTests == None:
        swapTests = DEFAULT_POOL_SWAP_TESTS
    else:
        swapTests = poolFixture.swapTests

    for testCase in swapTests:
        slot0 = pool.slot0
        poolInstance = copy.deepcopy(pool)

        # Get snapshot results
        snapshotIndex = swapsSnapshot.index(
            "UniswapV3Pool swap tests "
            + poolFixture.description
            + " "
            + swapCaseToDescription(testCase)
        )
        dict = swapsSnapshot[snapshotIndex + 1]

        try:
            recipient, amount0, amount1, _, _, _ = executeSwap(
                poolInstance, testCase, recipient
            )
        except AssertionError as msg:
            assert str(msg) == "SPL"
            assert float(dict["poolBalance0"]) == pytest.approx(poolBalance0, rel=1e-12)
            assert float(dict["poolBalance1"]) == pytest.approx(poolBalance1, rel=1e-12)
            decimalPoints = Decimal(dict["poolPriceBefore"]).as_tuple().exponent
            assert float(dict["poolPriceBefore"]) == formatPriceWithPrecision(
                slot0.sqrtPriceX96, -decimalPoints
            )
            assert float(dict["tickBefore"]) == slot0.tick
            continue

        poolBalance0After = poolInstance.balances[TEST_TOKENS[0]]
        poolBalance1After = poolInstance.balances[TEST_TOKENS[1]]
        slot0After = poolInstance.slot0
        liquidityAfter = poolInstance.liquidity
        feeGrowthGlobal0X128 = poolInstance.feeGrowthGlobal0X128
        feeGrowthGlobal1X128 = poolInstance.feeGrowthGlobal1X128

        poolBalance0Delta = poolBalance0After - poolBalance0
        poolBalance1Delta = poolBalance1After - poolBalance1

        ## check all the events were emitted corresponding to balance changes
        assert amount0 == poolBalance0Delta
        assert amount1 == poolBalance1Delta

        if poolBalance0Delta != 0:
            executionPrice = -(poolBalance1Delta / poolBalance0Delta)
        else:
            executionPrice = "-Infinity"

        # Allowing some very small difference due to rounding errors
        assert float(dict["amount0Before"]) == pytest.approx(poolBalance0, rel=1e-12)
        assert float(dict["amount0Delta"]) == pytest.approx(
            poolBalance0Delta, rel=1e-12
        )
        assert float(dict["amount1Before"]) == pytest.approx(poolBalance1, rel=1e-12)
        assert float(dict["amount1Delta"]) == pytest.approx(
            poolBalance1Delta, rel=1e-12
        )
        if dict["executionPrice"] in ["Infinity", "-Infinity", "NaN"]:
            assert executionPrice in ["Infinity", "-Infinity", "NaN"]
        else:
            decimalPoints = Decimal(dict["executionPrice"]).as_tuple().exponent
            assert float(dict["executionPrice"]) == round(
                executionPrice, -decimalPoints
            )
        assert float(dict["feeGrowthGlobal0X128Delta"]) == pytest.approx(
            feeGrowthGlobal0X128, rel=1e-12
        )
        assert float(dict["feeGrowthGlobal1X128Delta"]) == pytest.approx(
            feeGrowthGlobal1X128, rel=1e-12
        )
        # Rounding pool storage variables to the same amount of decimal points as the snapshots
        decimalPoints = Decimal(dict["poolPriceAfter"]).as_tuple().exponent
        assert float(dict["poolPriceAfter"]) == formatPriceWithPrecision(
            slot0After.sqrtPriceX96, -decimalPoints
        )
        decimalPoints = Decimal(dict["poolPriceBefore"]).as_tuple().exponent
        assert float(dict["poolPriceBefore"]) == formatPriceWithPrecision(
            slot0.sqrtPriceX96, -decimalPoints
        )
        assert float(dict["tickAfter"]) == slot0After.tick
        assert float(dict["tickBefore"]) == slot0.tick


def executeSwap(pool, testCase, recipient):
    sqrtPriceLimit = (
        None
        if not testCase.__contains__("sqrtPriceLimit")
        else testCase["sqrtPriceLimit"]
    )
    if testCase.__contains__("exactOut"):
        if testCase["exactOut"]:
            if testCase["zeroForOne"]:
                return swap0ForExact1(
                    pool, testCase["amount1"], recipient, sqrtPriceLimit
                )
            else:
                return swap1ForExact0(
                    pool, testCase["amount0"], recipient, sqrtPriceLimit
                )
        else:
            if testCase["zeroForOne"]:
                return swapExact0For1(
                    pool, testCase["amount0"], recipient, sqrtPriceLimit
                )
            else:
                return swapExact1For0(
                    pool, testCase["amount1"], recipient, sqrtPriceLimit
                )
    else:
        if testCase["zeroForOne"]:
            return swapToLowerPrice(pool, recipient, testCase["sqrtPriceLimit"])
        else:
            return swapToHigherPrice(pool, recipient, testCase["sqrtPriceLimit"])


def swapCaseToDescription(testCase):
    priceClause = (
        " to price " + str(formatPrice(testCase["sqrtPriceLimit"]))
        if testCase.__contains__("sqrtPriceLimit")
        else ""
    )

    if testCase.__contains__("exactOut"):
        if testCase["exactOut"]:
            if testCase["zeroForOne"]:
                return (
                    "swap token0 for exactly "
                    + formatTokenAmount(testCase["amount1"])
                    + " token1"
                    + priceClause
                )
            else:
                return (
                    "swap token1 for exactly "
                    + formatTokenAmount(testCase["amount0"])
                    + " token0"
                    + priceClause
                )
        else:
            if testCase["zeroForOne"]:
                return (
                    "swap exactly "
                    + formatTokenAmount(testCase["amount0"])
                    + " token0 for token1"
                    + priceClause
                )
            else:
                return (
                    "swap exactly "
                    + formatTokenAmount(testCase["amount1"])
                    + " token1 for token0"
                    + priceClause
                )
    else:
        if testCase["zeroForOne"]:
            return "swap token0 for token1" + priceClause
        else:
            return "swap token1 for token0" + priceClause
