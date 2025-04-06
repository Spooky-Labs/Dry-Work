# alpaca_broker.py
import backtrader as bt
from alpaca.broker.client import BrokerClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

class AlpacaMinimalBroker(bt.BrokerBase):
    params = (
        ('api_key', None),
        ('secret_key', None),
        ('account_id', None),
    )
    
    def __init__(self):
        super().__init__()
        self._cash = 0
        self._value = 0
        self._orders = {}
        self._positions = {}
        
        # Initialize Alpaca client
        self.client = BrokerClient(
            api_key=self.p.api_key,
            secret_key=self.p.secret_key
        )
        
        # Get initial account state
        self.refresh_account()
    
    def refresh_account(self):
        account = self.client.get_account(self.p.account_id)
        self._cash = float(account.cash)
        self._value = float(account.equity)
        
        # Fetch positions
        positions = self.client.get_all_positions(self.p.account_id)
        self._positions = {p.symbol: {'size': float(p.qty), 'price': float(p.avg_entry_price)} 
                           for p in positions}
    
    def getcash(self):
        return self._cash
    
    def getvalue(self):
        return self._value
    
    def getposition(self, data):
        symbol = data._name
        position = self._positions.get(symbol, {'size': 0, 'price': 0})
        return bt.Position(position['size'], position['price'])
    
    def buy(self, owner, data, size, price=None, **kwargs):
        order = bt.BuyOrder(owner=owner, data=data, size=size)
        
        # Submit to Alpaca
        order_request = MarketOrderRequest(
            symbol=data._name,
            qty=size,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        
        try:
            alpaca_order = self.client.submit_order(
                account_id=self.p.account_id,
                order_data=order_request
            )
            self._orders[order.ref] = alpaca_order.id
            self.refresh_account()
        except Exception as e:
            print(f"Order error: {e}")
            order.reject()
            
        return order
    
    def sell(self, owner, data, size, price=None, **kwargs):
        order = bt.SellOrder(owner=owner, data=data, size=size)
        
        # Submit to Alpaca
        order_request = MarketOrderRequest(
            symbol=data._name,
            qty=size,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        
        try:
            alpaca_order = self.client.submit_order(
                account_id=self.p.account_id,
                order_data=order_request
            )
            self._orders[order.ref] = alpaca_order.id
            self.refresh_account()
        except Exception as e:
            print(f"Order error: {e}")
            order.reject()
            
        return order