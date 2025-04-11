import backtrader as bt
import logging

logger = logging.getLogger(__name__)

class Agent(bt.Strategy):
    params = (
        ('fast_period', 1),
        ('slow_period', 2),
    )
    
    def __init__(self):
        # Create indicators
        logger.info("Agent strategy initialized")
        for d in self.datas:
            d.fast_ma = bt.indicators.SMA(d, period=self.params.fast_period)
            d.slow_ma = bt.indicators.SMA(d, period=self.params.slow_period)
            d.crossover = bt.indicators.CrossOver(d.fast_ma, d.slow_ma)

    def prenext(self):
        logger.info("Pre-next method called")

    def nextstart(self):
        logger.info("Next Start method called")

    def next(self):
        logger.info("Next method called")
        for d in self.datas:
            logger.info(f"Checking data")
            size = int(self.broker.getcash() * 0.15 / d.close[0])
            self.buy(data=d, size=size)
            # if not self.getposition(d).size:  # No position
            #     if d.crossover > 0:  # Buy signal
            #         size = int(self.broker.getcash() * 0.15 / d.close[0])
            #         self.buy(data=d, size=size)
            #         logger.info(f"Bought: {size} of {d}")
            # elif d.crossover < 0:  # Sell signal
            #     self.close(data=d)
            #     logger.info(f"Sold: {size} of {d}")
