# Remove these credentials after development
api_key = "CKI6JH8CDEZIIO3T7BK5" # Broker Keys
secret_key = "X4TCzbWAcmkabqps7XRpc7vIk7oasVlmFwbdmCGo" # Broker secret key
account_id = "105830c9-e690-4549-8d66-3048a3c5c6a2" # Account ID for Eloquent Swanson ACCT #: 789220144
project_id = "the-farm-neutrino"
#!/usr/bin/env python3
import backtrader as bt
import logging
import time
import signal
import sys
import os
from datetime import datetime

# Import custom components
from data_feed import PubSubMarketDataFeed
from broker import AlpacaPaperTradingBroker
from agent.agent import Agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trading_agent')

# Global control flag for graceful shutdown
running = True

# Configuration
CONFIG = {
    'api_key': "CKI6JH8CDEZIIO3T7BK5",
    'secret_key': "X4TCzbWAcmkabqps7XRpc7vIk7oasVlmFwbdmCGo",
    'account_id': "105830c9-e690-4549-8d66-3048a3c5c6a2",
    'project_id': "the-farm-neutrino",
    'poll_interval': 1,  # seconds
}

def signal_handler(sig, frame):
    """Handle termination signals"""
    global running
    logger.info("Shutdown signal received")
    running = False

def write_heartbeat():
    """Write heartbeat file"""
    try:
        with open('heartbeat.txt', 'w') as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        logger.warning(f"Failed to write heartbeat: {e}")

def main():
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load symbols
    try:
        with open("symbols.txt", "r") as f:
            symbols = [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error reading symbols: {e}")
        return False
    
    if not symbols:
        logger.error("No symbols found")
        return False
    
    logger.info(f"Starting agent with {len(symbols)} symbols")
    
    # Initialize Backtrader
    cerebro = bt.Cerebro()
    cerebro.addstrategy(Agent)
    
    # Setup broker
    broker = AlpacaPaperTradingBroker(
        api_key=CONFIG['api_key'],
        secret_key=CONFIG['secret_key'],
        account_id=CONFIG['account_id']
    )
    cerebro.setbroker(broker)
    
    # Add data feeds (but don't start them manually)
    for symbol in symbols:
        topic_name = 'crypto-data' if '/' in symbol else 'market-data'
        data = PubSubMarketDataFeed(
            project_id=CONFIG['project_id'],
            topic_name=topic_name,
            symbol=symbol
        )
        cerebro.adddata(data, name=symbol)
        logger.info(f"Added data feed for {symbol}")
    
    # Store initial portfolio value
    starting_value = cerebro.broker.getvalue()
    logger.info(f"Initial portfolio value: ${starting_value:.2f}")
    
    # Start data feeds
    logger.info("Starting data feeds")
    for data in cerebro.datas:
        try:
            data.start()
        except Exception as e:
            logger.error(f"Error starting feed {data._name}: {e}")
    
    # Run strategy in live mode with proper settings
    logger.info("Running strategy in live mode")
    # KEY CHANGE: Don't run cerebro.run() immediately after starting feeds
    
    # Maintenance loop
    last_heartbeat = time.time()
    last_report = time.time()
    strategy_started = False
    
    logger.info(f"Entering maintenance loop (every {CONFIG['poll_interval']}s)")
    try:
        while running:
            logger.info(f"Running again")
            # Check if any data is available and start the strategy if not started yet
            if not strategy_started and any(len(data) > 0 for data in cerebro.datas):
                # Run strategy once when data becomes available
                cerebro.run(preload=False, runonce=False)
                strategy_started = True
            
            # Process broker activity
            cerebro.broker.notify()
            
            # Periodic tasks
            now = time.time()
            if now - last_heartbeat >= 300:  # Every 5 minutes
                write_heartbeat()
                last_heartbeat = now
                
            if now - last_report >= 3600:  # Every hour
                current_value = cerebro.broker.getvalue()
                pnl = current_value - starting_value
                logger.info(f"Portfolio value: ${current_value:.2f} (P&L: ${pnl:.2f})")
                last_report = now
            
            time.sleep(CONFIG['poll_interval'])
            
    except Exception as e:
        logger.error(f"Error in main loop: {e}", exc_info=True)
        return False
    finally:
        # Shutdown
        logger.info("Shutting down agent")
        for data in cerebro.datas:
            if hasattr(data, 'stop'):
                try:
                    data.stop()
                except Exception as e:
                    logger.error(f"Error stopping feed: {e}")
        
        logger.info("Agent shutdown complete")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)