from .Shared import checkInputTypes
from ..UniswapPool import *

## @title Pool factory
## @notice Deploys Uniswap V3 pools and manages ownership and control over pool protocol fees
class Factory:
    def __init__(self):
        self.feeAmountTickSpacing = {500: 10, 3000: 60, 10000: 200}
        self.getPool = []

    ## @notice Creates a pool for the given two tokens and fee
    ## @param tokenA One of the two tokens in the desired pool
    ## @param tokenB The other of the two tokens in the desired pool
    ## @param fee The desired fee for the pool
    ## @param ledger Reference to the ledger
    ## @dev tokenA and tokenB may be passed in either order: token0/token1 or token1/token0. tickSpacing is retrieved
    ## from the fee. The call will revert if the pool already exists, the fee is invalid, or the token arguments
    ## are invalid.
    ## @return pool The address of the newly created pool
    def createPool(self, tokenA, tokenB, fee, ledger):
        checkInputTypes(string=(tokenA, tokenB), uint24=(fee))
        assert tokenA != tokenB

        (token0, token1) = (tokenA, tokenB) if tokenA < tokenB else (tokenB, tokenA)
        assert token0 != "0"
        assert self.feeAmountTickSpacing.__contains__(fee), "Fee amount not supported"
        assert self.feeAmountTickSpacing[fee] != 0
        tickSpacing = self.feeAmountTickSpacing[fee]

        if [token0, token1, fee] not in self.getPool:
            self.getPool.append([token0, token1, fee])
        else:
            assert False, "Pool already exists"

        pool = UniswapPool(token0, token1, fee, tickSpacing, ledger)

        return pool

    ## @notice Enables a fee amount with the given tickSpacing
    ## @dev Fee amounts may never be removed once enabled
    ## @param fee The fee amount to enable, denominated in hundredths of a bip (i.e. 1e-6)
    ## @param tickSpacing The spacing between ticks to be enforced for all pools created with the given fee amount
    def enableFeeAmount(self, fee, tickSpacing):
        checkInputTypes(uint24=(fee), int24=(tickSpacing))
        assert fee < 1000000
        ## tick spacing is capped at 16384 to prevent the situation where tickSpacing is so large that
        ## TickBitmap#nextInitializedTickWithinOneWord overflows int24 container from a valid tick
        ## 16384 ticks represents a >5x price change with ticks of 1 bips
        assert tickSpacing > 0 and tickSpacing < 16384
        assert (
            not self.feeAmountTickSpacing.__contains__(fee)
            or self.feeAmountTickSpacing[fee] == 0
        )
        self.feeAmountTickSpacing[fee] = tickSpacing
