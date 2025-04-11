import backtrader as bt
import logging

logger = logging.getLogger(__name__)

class Agent(bt.Strategy):
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
    )
    
    def __init__(self):
        # Create indicators
        logger.info("Agent strategy initialized")
        for d in self.datas:
            d.fast_ma = bt.indicators.SMA(d, period=self.params.fast_period)
            d.slow_ma = bt.indicators.SMA(d, period=self.params.slow_period)
            d.crossover = bt.indicators.CrossOver(d.fast_ma, d.slow_ma)
    
    def next(self):
        logger.info("Agent Working")
        for d in self.datas:
            if not self.getposition(d).size:  # No position
                if d.crossover > 0:  # Buy signal
                    size = int(self.broker.getcash() * 0.15 / d.close[0])
                    self.buy(data=d, size=size)
            elif d.crossover < 0:  # Sell signal
                self.close(data=d)

    def notify_data(self, data, status, *args, **kwargs):
        """Receives data notifications about status changes"""
        logger.info(f"**** DATA NOTIFICATION: {data._name} - {data._getstatusname(status)}")
        if status == data.LIVE:
            logger.info(f"DATA LIVE: {data._name}")
        elif status == data.DISCONNECTED:
            logger.info(f"DATA DISCONNECTED: {data._name}")