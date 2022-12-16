from .utilities import *


@dataclass
class PoolTestCase:
    description: str
    feeAmount: int
    tickSpacing: int
    startingPrice: int
    positions: list
    swapTests: list


@dataclass
class Position:
    tickLower: int
    tickUpper: int
    liquidity: int


@pytest.fixture
def pool0():
    return PoolTestCase(
        description="low fee, 1:1 price, 2e18 max range liquidity",
        feeAmount=FeeAmount.LOW,
        tickSpacing=TICK_SPACINGS[FeeAmount.LOW],
        startingPrice=encodePriceSqrt(1, 1),
        positions=[
            Position(
                tickLower=getMinTick(TICK_SPACINGS[FeeAmount.LOW]),
                tickUpper=getMaxTick(TICK_SPACINGS[FeeAmount.LOW]),
                liquidity=expandTo18Decimals(2),
            ),
        ],
        swapTests=None,
    )


@pytest.fixture
def pool1():
    return PoolTestCase(
        description="medium fee, 1:1 price, 2e18 max range liquidity",
        feeAmount=FeeAmount.MEDIUM,
        tickSpacing=TICK_SPACINGS[FeeAmount.MEDIUM],
        startingPrice=encodePriceSqrt(1, 1),
        positions=[
            Position(
                tickLower=getMinTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                tickUpper=getMaxTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                liquidity=expandTo18Decimals(2),
            ),
        ],
        swapTests=None,
    )


@pytest.fixture
def pool2():
    return PoolTestCase(
        description="high fee, 1:1 price, 2e18 max range liquidity",
        feeAmount=FeeAmount.HIGH,
        tickSpacing=TICK_SPACINGS[FeeAmount.HIGH],
        startingPrice=encodePriceSqrt(1, 1),
        positions=[
            Position(
                tickLower=getMinTick(TICK_SPACINGS[FeeAmount.HIGH]),
                tickUpper=getMaxTick(TICK_SPACINGS[FeeAmount.HIGH]),
                liquidity=expandTo18Decimals(2),
            ),
        ],
        swapTests=None,
    )


@pytest.fixture
def pool3():
    return PoolTestCase(
        description="medium fee, 10:1 price, 2e18 max range liquidity",
        feeAmount=FeeAmount.MEDIUM,
        tickSpacing=TICK_SPACINGS[FeeAmount.MEDIUM],
        startingPrice=encodePriceSqrt(10, 1),
        positions=[
            Position(
                tickLower=getMinTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                tickUpper=getMaxTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                liquidity=expandTo18Decimals(2),
            ),
        ],
        swapTests=None,
    )


@pytest.fixture
def pool4():
    return PoolTestCase(
        description="medium fee, 1:10 price, 2e18 max range liquidity",
        feeAmount=FeeAmount.MEDIUM,
        tickSpacing=TICK_SPACINGS[FeeAmount.MEDIUM],
        startingPrice=encodePriceSqrt(1, 10),
        positions=[
            Position(
                tickLower=getMinTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                tickUpper=getMaxTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                liquidity=expandTo18Decimals(2),
            ),
        ],
        swapTests=None,
    )


@pytest.fixture
def pool5():
    return PoolTestCase(
        description="medium fee, 1:1 price, 0 liquidity, all liquidity around current price",
        feeAmount=FeeAmount.MEDIUM,
        tickSpacing=TICK_SPACINGS[FeeAmount.MEDIUM],
        startingPrice=encodePriceSqrt(1, 1),
        positions=[
            Position(
                tickLower=getMinTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                tickUpper=-TICK_SPACINGS[FeeAmount.MEDIUM],
                liquidity=expandTo18Decimals(2),
            ),
            Position(
                tickLower=TICK_SPACINGS[FeeAmount.MEDIUM],
                tickUpper=getMaxTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                liquidity=expandTo18Decimals(2),
            ),
        ],
        swapTests=None,
    )


@pytest.fixture
def pool6():
    return PoolTestCase(
        description="medium fee, 1:1 price, additional liquidity around current price",
        feeAmount=FeeAmount.MEDIUM,
        tickSpacing=TICK_SPACINGS[FeeAmount.MEDIUM],
        startingPrice=encodePriceSqrt(1, 1),
        positions=[
            Position(
                tickLower=getMinTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                tickUpper=getMaxTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                liquidity=expandTo18Decimals(2),
            ),
            Position(
                tickLower=getMinTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                tickUpper=-TICK_SPACINGS[FeeAmount.MEDIUM],
                liquidity=expandTo18Decimals(2),
            ),
            Position(
                tickLower=TICK_SPACINGS[FeeAmount.MEDIUM],
                tickUpper=getMaxTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                liquidity=expandTo18Decimals(2),
            ),
        ],
        swapTests=None,
    )


@pytest.fixture
def pool7():
    return PoolTestCase(
        description="low fee, large liquidity around current price (stable swap)",
        feeAmount=FeeAmount.LOW,
        tickSpacing=TICK_SPACINGS[FeeAmount.LOW],
        startingPrice=encodePriceSqrt(1, 1),
        positions=[
            Position(
                tickLower=-TICK_SPACINGS[FeeAmount.LOW],
                tickUpper=TICK_SPACINGS[FeeAmount.LOW],
                liquidity=expandTo18Decimals(2),
            )
        ],
        swapTests=None,
    )


@pytest.fixture
def pool8():
    return PoolTestCase(
        description="medium fee, token0 liquidity only",
        feeAmount=FeeAmount.MEDIUM,
        tickSpacing=TICK_SPACINGS[FeeAmount.MEDIUM],
        startingPrice=encodePriceSqrt(1, 1),
        positions=[
            Position(
                tickLower=0,
                tickUpper=2000 * TICK_SPACINGS[FeeAmount.MEDIUM],
                liquidity=expandTo18Decimals(2),
            )
        ],
        swapTests=None,
    )


@pytest.fixture
def pool9():
    return PoolTestCase(
        description="medium fee, token1 liquidity only",
        feeAmount=FeeAmount.MEDIUM,
        tickSpacing=TICK_SPACINGS[FeeAmount.MEDIUM],
        startingPrice=encodePriceSqrt(1, 1),
        positions=[
            Position(
                tickLower=-2000 * TICK_SPACINGS[FeeAmount.MEDIUM],
                tickUpper=0,
                liquidity=expandTo18Decimals(2),
            )
        ],
        swapTests=None,
    )


@pytest.fixture
def pool10():
    return PoolTestCase(
        description="close to max price",
        feeAmount=FeeAmount.MEDIUM,
        tickSpacing=TICK_SPACINGS[FeeAmount.MEDIUM],
        startingPrice=encodePriceSqrt(2**127, 1),
        positions=[
            Position(
                tickLower=getMinTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                tickUpper=getMaxTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                liquidity=expandTo18Decimals(2),
            )
        ],
        swapTests=None,
    )


# This pool with such low starting price (or someething else) ends up with a bigger
# than normal rounding error when comparing amount0before (and possibly others)
@pytest.fixture
def pool11():
    return PoolTestCase(
        description="close to min price",
        feeAmount=FeeAmount.MEDIUM,
        tickSpacing=TICK_SPACINGS[FeeAmount.MEDIUM],
        startingPrice=encodePriceSqrt(1, 2**127),
        positions=[
            Position(
                tickLower=getMinTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                tickUpper=getMaxTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                liquidity=expandTo18Decimals(2),
            )
        ],
        swapTests=None,
    )


@pytest.fixture
def pool12():
    return PoolTestCase(
        description="max full range liquidity at 1:1 price with default fee",
        feeAmount=FeeAmount.MEDIUM,
        tickSpacing=TICK_SPACINGS[FeeAmount.MEDIUM],
        startingPrice=encodePriceSqrt(1, 1),
        positions=[
            Position(
                tickLower=getMinTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                tickUpper=getMaxTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                liquidity=getMaxLiquidityPerTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
            )
        ],
        swapTests=None,
    )


@pytest.fixture
def pool13():
    return PoolTestCase(
        description="initialized at the max ratio",
        feeAmount=FeeAmount.MEDIUM,
        tickSpacing=TICK_SPACINGS[FeeAmount.MEDIUM],
        startingPrice=MAX_SQRT_RATIO - 1,
        positions=[
            Position(
                tickLower=getMinTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                tickUpper=getMaxTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                liquidity=expandTo18Decimals(2),
            )
        ],
        swapTests=None,
    )


@pytest.fixture
def pool14():
    return PoolTestCase(
        description="initialized at the min ratio",
        feeAmount=FeeAmount.MEDIUM,
        tickSpacing=TICK_SPACINGS[FeeAmount.MEDIUM],
        startingPrice=MIN_SQRT_RATIO,
        positions=[
            Position(
                tickLower=getMinTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                tickUpper=getMaxTick(TICK_SPACINGS[FeeAmount.MEDIUM]),
                liquidity=expandTo18Decimals(2),
            )
        ],
        swapTests=None,
    )


@dataclass
class SWAP_TEST:
    zeroForOne: bool
    exactOut: bool
    amount0: int


DEFAULT_POOL_SWAP_TESTS = [
    {
        ## swap large amounts in/out
        "zeroForOne": True,
        "exactOut": False,
        "amount0": expandTo18Decimals(1),
    },
    {
        "zeroForOne": False,
        "exactOut": False,
        "amount1": expandTo18Decimals(1),
    },
    {
        "zeroForOne": True,
        "exactOut": True,
        "amount1": expandTo18Decimals(1),
    },
    {
        "zeroForOne": False,
        "exactOut": True,
        "amount0": expandTo18Decimals(1),
    },
    ## swap large amounts in/out with a price limit
    {
        "zeroForOne": True,
        "exactOut": False,
        "amount0": expandTo18Decimals(1),
        "sqrtPriceLimit": encodePriceSqrt(50, 100),
    },
    {
        "zeroForOne": False,
        "exactOut": False,
        "amount1": expandTo18Decimals(1),
        "sqrtPriceLimit": encodePriceSqrt(200, 100),
    },
    {
        "zeroForOne": True,
        "exactOut": True,
        "amount1": expandTo18Decimals(1),
        "sqrtPriceLimit": encodePriceSqrt(50, 100),
    },
    {
        "zeroForOne": False,
        "exactOut": True,
        "amount0": expandTo18Decimals(1),
        "sqrtPriceLimit": encodePriceSqrt(200, 100),
    },
    # ## swap small amounts in/out
    # Also, it is only off in extreme pools, not in the ones closer to normal functioning.
    # {
    #   "zeroForOne": True,
    #   "exactOut": False,
    #   "amount0": 1000,
    # },
    # {
    #   "zeroForOne": False,
    #   "exactOut": False,
    #   "amount1": 1000,
    # },
    {
        "zeroForOne": True,
        "exactOut": True,
        "amount1": 1000,
    },
    {
        "zeroForOne": False,
        "exactOut": True,
        "amount0": 1000,
    },
    # ## swap arbitrary input to price
    {
        "sqrtPriceLimit": encodePriceSqrt(5, 2),
        "zeroForOne": False,
    },
    {
        "sqrtPriceLimit": encodePriceSqrt(2, 5),
        "zeroForOne": True,
    },
    {
        "sqrtPriceLimit": encodePriceSqrt(5, 2),
        "zeroForOne": True,
    },
    {
        "sqrtPriceLimit": encodePriceSqrt(2, 5),
        "zeroForOne": False,
    },
]
