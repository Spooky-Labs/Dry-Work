import backtrader as bt

class Agent(bt.Strategy):
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
    )
    
    def __init__(self):
        # Create indicators
        for d in self.datas:
            d.fast_ma = bt.indicators.SMA(d, period=self.params.fast_period)
            d.slow_ma = bt.indicators.SMA(d, period=self.params.slow_period)
            d.crossover = bt.indicators.CrossOver(d.fast_ma, d.slow_ma)
    
    def next(self):
        print(f"[{self.datetime.datetime(0)}] Got bar for {self.datas[0]._name}: close={self.datas[0].close[0]}")
        for d in self.datas:
            if not self.getposition(d).size:  # No position
                if d.crossover > 0:  # Buy signal
                    size = int(self.broker.getcash() * 0.15 / d.close[0])
                    self.buy(data=d, size=size)
            elif d.crossover < 0:  # Sell signal
                self.close(data=d)