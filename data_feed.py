# data_feed.py
import backtrader as bt
import json
import queue
from datetime import datetime
from google.cloud import pubsub_v1

class DynamicPubSubFeed(bt.feeds.DataBase):
    """
    Data feed that automatically exposes all fields from PubSub messages
    as Backtrader lines, making them directly accessible to the strategy.
    """
    
    params = (
        ('project_id', None),     # GCP project ID
        ('topic_name', None),     # Pub/Sub topic name
        ('symbol', None),         # Symbol to filter messages
    )
    
    def __init__(self):
        super().__init__()
        
        # Initialize standard OHLCV lines
        self.lines.datetime = 0
        self.lines.open = 0
        self.lines.high = 0
        self.lines.low = 0
        self.lines.close = 0
        self.lines.volume = 0
        self.lines.openinterest = 0
        
        # Set up data buffer and track discovered fields
        self._data_buffer = queue.Queue()
        self._discovered_fields = set()
        self._running = False
        self._subscription = None
    
    def start(self):
        """Start receiving data from Pub/Sub"""
        if self._running:
            return
        
        # Set up the subscription
        subscriber = pubsub_v1.SubscriberClient()
        topic_path = f"projects/{self.p.project_id}/topics/{self.p.topic_name}"
        subscription_id = f"feed-{self.p.symbol}-{id(self)}"
        subscription_path = f"projects/{self.p.project_id}/subscriptions/{subscription_id}"
        
        # Create subscription if needed
        try:
            subscriber.get_subscription(subscription=subscription_path)
        except Exception:
            subscriber.create_subscription(
                request={
                    "name": subscription_path,
                    "topic": topic_path,
                    "filter": f"attributes.symbol = \"{self.p.symbol}\""
                }
            )
        
        # Define message handler
        def callback(message):
            try:
                data = json.loads(message.data.decode('utf-8'))
                self._data_buffer.put(data)
                message.ack()
                
                # Check for new fields to add dynamically
                self._check_new_fields(data)
            except Exception as e:
                print(f"Error processing message: {e}")
                message.nack()
        
        # Start subscription
        self._subscription = subscriber.subscribe(
            subscription_path, callback=callback
        )
        self._running = True
    
    def _check_new_fields(self, data):
        """Check for new fields in the message and add lines for them"""
        for field_name, value in data.items():
            # Skip standard fields and non-numeric values
            if field_name in ('open', 'high', 'low', 'close', 'volume', 'timestamp'):
                continue
                
            if field_name not in self._discovered_fields and isinstance(value, (int, float)):
                self._discovered_fields.add(field_name)
                
                # Create a new line for this field
                self.addline(field_name)
                
                # Initialize with default value
                line = getattr(self.lines, field_name)
                line[0] = 0
    
    def stop(self):
        """Stop receiving data"""
        if not self._running:
            return
        
        # Cancel subscription
        if self._subscription:
            self._subscription.cancel()
        
        self._running = False
    
    def _load(self):
        """Called by Backtrader when it needs new data"""
        if not self._running or self._data_buffer.empty():
            return False
        
        # Get next message from buffer
        data = self._data_buffer.get()
        
        # Always update datetime (required by Backtrader)
        timestamp = datetime.fromisoformat(data.get('timestamp', '').replace('Z', '+00:00'))
        self.lines.datetime[0] = bt.date2num(timestamp)
        
        # Update standard price fields if present
        if 'open' in data: self.lines.open[0] = float(data['open'])
        if 'high' in data: self.lines.high[0] = float(data['high']) 
        if 'low' in data: self.lines.low[0] = float(data['low'])
        if 'close' in data: self.lines.close[0] = float(data['close'])
        if 'volume' in data: self.lines.volume[0] = float(data['volume'])
        
        # Update any additional fields
        for field_name in self._discovered_fields:
            if field_name in data and hasattr(self.lines, field_name):
                line = getattr(self.lines, field_name)
                line[0] = float(data.get(field_name, 0))
        
        return True