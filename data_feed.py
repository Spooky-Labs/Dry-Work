import backtrader as bt
import json
import queue
import logging
from datetime import datetime, timezone
from google.cloud import pubsub_v1

logger = logging.getLogger(__name__)

class PubSubMarketDataFeed(bt.feeds.DataBase):
    """
    Simplified data feed that consumes market data from Google Cloud Pub/Sub.
    Focuses on core OHLCV data for reliable operation.
    """
    
    # Define the lines
    lines = ('open', 'high', 'low', 'close', 'volume')
    
    # Define parameters
    params = (
        ('project_id', None),     # GCP project ID
        ('topic_name', None),     # Pub/Sub topic name
        ('symbol', None),         # Symbol to filter messages
    )
    
    def __init__(self):
        # Call parent class constructor
        super(PubSubMarketDataFeed, self).__init__()
        
        # For Live Trading
        self._laststatus = self.LIVE

        # Data buffer for incoming messages
        self._data_buffer = queue.Queue()
        self._subscription = None
        self._subscriber = None
        self._subscription_path = None
        self._running = False
        
        logger.info(f"Initialized PubSub data feed for {self.p.symbol}")

    def islive(self):
        return True
    
    def haslivedata(self):
        return True
    
    def start(self):
        """Set up Pub/Sub subscription and start receiving data"""
        if self._running:
            logger.warning(f"Data feed for {self.p.symbol} already running")
            return
            
        if not all([self.p.project_id, self.p.topic_name, self.p.symbol]):
            raise ValueError("Missing required parameter: project_id, topic_name, or symbol")
        
        try:
            # Create a subscriber client
            self._subscriber = pubsub_v1.SubscriberClient()
            
            # Define topic and subscription paths
            topic_path = f"projects/{self.p.project_id}/topics/{self.p.topic_name}"
            
            # Create a unique subscription for this feed instance
            subscription_id = f"feed-{self.p.symbol.replace("/", "-")}-{id(self):x}"
            self._subscription_path = f"projects/{self.p.project_id}/subscriptions/{subscription_id}"
            
            # Create subscription with a filter for the specific symbol
            try:
                self._subscriber.create_subscription(
                    request={
                        "name": self._subscription_path,
                        "topic": topic_path,
                        "filter": f"attributes.symbol = \"{self.p.symbol.replace("/", "-")}\"",
                        "expiration_policy": {"ttl": {"seconds": 86400}}  # Auto-delete after 24 hours (minimum required)
                    }
                )
                logger.info(f"Created subscription: {self._subscription_path}")
            except Exception as e:
                logger.error(f"Error creating subscription: {e}")
                raise
            
            # Define the callback function for handling messages
            def handle_message(message):
                try:
                    # Decode message data
                    logger.info(f"[HANDLE_MESSAGE] Received for {self.p.symbol}: {message.data}")

                    data_str = message.data.decode('utf-8')
                    data = json.loads(data_str)
                    
                    # Add to buffer
                    self._data_buffer.put(data)
                    
                    # Acknowledge the message
                    message.ack()
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in message: {message.data}")
                    message.nack()
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    message.nack()
            
            # Start the subscription
            logger.info(f"Starting subscription for {self.p.symbol}")
            self._subscription = self._subscriber.subscribe(
                self._subscription_path, callback=handle_message
            )
            
            self._running = True
            logger.info(f"Data feed started for {self.p.symbol}")
            
        except Exception as e:
            logger.error(f"Failed to start data feed: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Clean up resources"""
        if not self._running:
            return
            
        logger.info(f"Stopping data feed for {self.p.symbol}")
        
        # Cancel subscription
        if self._subscription:
            self._subscription.cancel()
            self._subscription = None
        
        # Delete the subscription
        if self._subscriber and self._subscription_path:
            try:
                self._subscriber.delete_subscription(
                    request={"subscription": self._subscription_path}
                )
                logger.info(f"Deleted subscription: {self._subscription_path}")
            except Exception as e:
                logger.warning(f"Failed to delete subscription: {e}")
        
        # Close subscriber client
        if self._subscriber:
            self._subscriber.close()
            self._subscriber = None
            
        self._running = False
        logger.info(f"Data feed stopped for {self.p.symbol}")
    
    def _load(self):
        """
        Called by Backtrader when it needs new data.
        Returns True if new data was loaded, False otherwise.
        """

        # if not getattr(self, '_st_start', False):
        #     self._st_start = True
        self._laststatus = self.LIVE

        if not self._running:
            logger.warning(f"Data feed not running for {self.p.symbol}")
            return False
            
        if self._data_buffer.empty():
            return False
        
        try:
            # Get next message from buffer
            data = self._data_buffer.get(block=False)
            
            # Update datetime (required by Backtrader)
            if 'timestamp' in data:
                try:
                    # Parse timestamp, assuming ISO format with potential timezone info
                    timestamp_str = data['timestamp']
                    # Handle timestamp with or without timezone
                    if timestamp_str.endswith('Z'):
                        timestamp_str = timestamp_str.replace('Z', '+00:00')
                    
                    dt = datetime.fromisoformat(timestamp_str)
                    # Ensure timezone is set if not already
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                        
                    # Convert to Backtrader's numeric format
                    self.lines.datetime[0] = bt.date2num(dt)
                except ValueError as e:
                    logger.error(f"Invalid timestamp format in message: {e}")
                    return False
            else:
                # If no timestamp, use current time
                self.lines.datetime[0] = bt.date2num(datetime.now(timezone.utc))
            
            # Update price data
            try:
                if 'open' in data:
                    self.lines.open[0] = float(data['open'])
                if 'high' in data:
                    self.lines.high[0] = float(data['high'])
                if 'low' in data:
                    self.lines.low[0] = float(data['low'])
                if 'close' in data:
                    self.lines.close[0] = float(data['close'])
                if 'volume' in data:
                    self.lines.volume[0] = float(data['volume'])
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid data format in message: {e}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False