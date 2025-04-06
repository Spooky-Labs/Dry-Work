# alpaca_feed.py
import backtrader as bt
import pandas as pd
from datetime import datetime, timedelta
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

class AlpacaMinimalData(bt.feeds.DataBase):
    params = (
        ('api_key', None),
        ('secret_key', None),
        ('symbol', None),
        ('timeframe', TimeFrame.Day),
        ('fromdate', None),
        ('todate', None),
    )
    
    def __init__(self):
        super().__init__()
        
        # Initialize Alpaca client
        self.client = StockHistoricalDataClient(
            api_key=self.p.api_key,
            secret_key=self.p.secret_key
        )
        
        # Set data line names
        self.lines.datetime = 0
        self.lines.open = 0
        self.lines.high = 0
        self.lines.low = 0
        self.lines.close = 0
        self.lines.volume = 0
        self.lines.openinterest = 0
        
        # Set additional metadata
        self._name = self.p.symbol
        self.data = None
        self.idx = -1
    
    def start(self):
        # Request historical data from Alpaca
        todate = self.p.todate or datetime.now()
        fromdate = self.p.fromdate or (todate - timedelta(days=30))
        
        bars_request = StockBarsRequest(
            symbol_or_symbols=self.p.symbol,
            timeframe=self.p.timeframe,
            start=fromdate,
            end=todate
        )
        
        bars_data = self.client.get_stock_bars(bars_request)
        
        # Convert to dataframe and prepare for backtrader
        if bars_data.data:
            df = bars_data.df
            if isinstance(df.index, pd.MultiIndex):
                df = df.loc[self.p.symbol].copy()
                
            df = df.sort_index()
            self.data = df
            self.idx = -1
    
    def _load(self):
        if self.data is None or self.idx >= len(self.data) - 1:
            return False
            
        self.idx += 1
        row = self.data.iloc[self.idx]
        
        # Parse timestamp
        dt = pd.to_datetime(self.data.index[self.idx])
        timestamp = bt.date2num(dt.to_pydatetime())
        
        # Update lines
        self.lines.datetime[0] = timestamp
        self.lines.open[0] = row['open']
        self.lines.high[0] = row['high']
        self.lines.low[0] = row['low']
        self.lines.close[0] = row['close']
        self.lines.volume[0] = row['volume']
        self.lines.openinterest[0] = 0
        
        return True