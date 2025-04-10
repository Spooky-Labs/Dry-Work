# broker.py
import backtrader as bt
import logging
from alpaca.broker.client import BrokerClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus

class AlpacaPaperTradingBroker(bt.BrokerBase):
    """Minimalist broker implementation for Alpaca Paper Trading"""
    
    params = (
        ('api_key', None),          # Alpaca API key
        ('secret_key', None),       # Alpaca API secret 
        ('account_id', None),       # Alpaca account ID
    )
    
    def __init__(self):
        super().__init__()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize state
        self._cash = 0
        self._value = 0
        self._orders = {}  # backtrader order ref -> alpaca order
        self._positions = {}
        
        # Initialize Alpaca client
        self.client = BrokerClient(
            api_key=self.p.api_key,
            secret_key=self.p.secret_key
        )
        
        # Get initial account state
        self.refresh_account()
    
    def refresh_account(self):
        """Fetch latest account information from Alpaca"""
        try:
            # Get account details
            account = self.client.get_account(self.p.account_id)
            self._cash = float(account.cash)
            self._value = float(account.equity)
            
            # Fetch current positions
            positions = self.client.get_all_positions(self.p.account_id)
            self._positions = {
                p.symbol: {
                    'size': float(p.qty), 
                    'price': float(p.avg_entry_price)
                } for p in positions
            }
            
            return True
        except Exception as e:
            self.logger.error(f"Error refreshing account: {e}")
            return False
    
    def getcash(self):
        """Return available cash"""
        return self._cash
    
    def getvalue(self):
        """Return total portfolio value"""
        return self._value
    
    def getposition(self, data):
        """Get position for the given asset"""
        symbol = data._name
        position = self._positions.get(symbol, {'size': 0, 'price': 0})
        return bt.Position(position['size'], position['price'])
    
    def buy(self, owner, data, size, price=None, exectype=None, **kwargs):
        """Create a buy order"""
        order = self._create_order(
            owner=owner, 
            data=data, 
            size=size,
            price=price,
            side=OrderSide.BUY,
            exectype=exectype,
            **kwargs
        )
        return order
    
    def sell(self, owner, data, size, price=None, exectype=None, **kwargs):
        """Create a sell order"""
        order = self._create_order(
            owner=owner, 
            data=data, 
            size=size,
            price=price,
            side=OrderSide.SELL,
            exectype=exectype,
            **kwargs
        )
        return order
    
    def _create_order(self, owner, data, size, price, side, exectype=None, **kwargs):
        """Unified order creation logic"""
        # Create Backtrader order
        if side == OrderSide.BUY:
            order = bt.BuyOrder(owner=owner, data=data, size=size, 
                               price=price, exectype=exectype)
        else:
            order = bt.SellOrder(owner=owner, data=data, size=size, 
                                price=price, exectype=exectype)
        
        # Determine order type
        is_market = price is None or exectype is None or exectype == bt.Order.Market
        
        try:
            if is_market:
                # Create market order
                order_request = MarketOrderRequest(
                    symbol=data._name,
                    qty=size,
                    side=side,
                    time_in_force=TimeInForce.DAY
                )
            else:
                # Create limit order
                order_request = LimitOrderRequest(
                    symbol=data._name,
                    qty=size,
                    side=side,
                    time_in_force=TimeInForce.DAY,
                    limit_price=price
                )
            
            # Submit order to Alpaca
            alpaca_order = self.client.submit_order(
                account_id=self.p.account_id,
                order_data=order_request
            )
            
            # Store order reference
            self._orders[order.ref] = alpaca_order.id
            
            # Always refresh account after order submission
            self.refresh_account()
            
        except Exception as e:
            self.logger.error(f"Order submission error: {e}")
            order.reject()
        
        return order
    
    def cancel(self, order):
        """Cancel an order"""
        if order.ref not in self._orders:
            return False
        
        try:
            alpaca_order_id = self._orders[order.ref]
            self.client.cancel_order(
                account_id=self.p.account_id,
                order_id=alpaca_order_id
            )
            order.cancel()
            self.refresh_account()
            return True
        except Exception as e:
            self.logger.error(f"Cancel order error: {e}")
            return False
    
    def check_order_status(self, order):
        """Check current status of an order"""
        if order.ref not in self._orders:
            return None
        
        try:
            alpaca_order_id = self._orders[order.ref]
            alpaca_order = self.client.get_order(
                account_id=self.p.account_id,
                order_id=alpaca_order_id
            )
            
            # Map Alpaca status to Backtrader status
            if alpaca_order.status == OrderStatus.FILLED:
                order.completed()
                self.refresh_account()
            elif alpaca_order.status == OrderStatus.CANCELED:
                order.cancel()
            elif alpaca_order.status == OrderStatus.REJECTED:
                order.reject()
            
            return alpaca_order.status
        except Exception as e:
            self.logger.error(f"Check order status error: {e}")
            return None