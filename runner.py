# Remove these credentials after development
api_key = "CKI6JH8CDEZIIO3T7BK5" # Broker Keys
secret_key = "X4TCzbWAcmkabqps7XRpc7vIk7oasVlmFwbdmCGo" # Broker secret key
account_id = "105830c9-e690-4549-8d66-3048a3c5c6a2" # Account ID for Eloquent Swanson ACCT #: 789220144
project_id = "the-farm-neutrino"
# api_key = os.environ.get('ALPACA_API_KEY')
# secret_key = os.environ.get('ALPACA_SECRET_KEY')
# account_id = os.environ.get('ALPACA_ACCOUNT_ID')
# project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')

#!/usr/bin/env python3
import backtrader as bt
import logging
import time
import signal
import sys
import os
from datetime import datetime

# Import our custom components
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

def wait_for_first_bar(cerebro, timeout=30):
    log = logging.getLogger("trading_agent")
    start = time.time()
    while all(len(data) == 0 for data in cerebro.datas):
        if time.time() - start > timeout:
            log.warning("Timeout waiting for bars — continuing anyway.")
            break
        time.sleep(0.5)
    log.info("Bar received — running strategy.")

def signal_handler(sig, frame):
    """Handle termination signals for graceful shutdown"""
    global running
    logger.info("Shutdown signal received")
    running = False

def write_heartbeat():
    """Write a heartbeat file for health checks"""
    try:
        os.makedirs('/var/lib/trading-agent', exist_ok=True)
        heartbeat_file = '/var/lib/trading-agent/heartbeat'
        with open(heartbeat_file, 'w') as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        logger.warning(f"Failed to write heartbeat: {e}")

def get_symbols():
    """Read symbols from the symbols.txt file"""
    try:
        with open("symbols.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error reading symbols file: {e}")
        return []

def run_agent():
    """Main function to run the trading agent"""
    # Get configuration from environment variables
    # api_key = os.environ.get('ALPACA_API_KEY')
    # secret_key = os.environ.get('ALPACA_SECRET_KEY')
    # account_id = os.environ.get('ALPACA_ACCOUNT_ID')
    # project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    
    # Default poll interval 60 seconds
    poll_interval = float(os.environ.get('POLL_INTERVAL', '60'))
    
    # Validate configuration 
    if not all([api_key, secret_key, account_id, project_id]):
        logger.error("Missing required environment variables")
        return False
    
    # Get symbols to trade
    symbols = get_symbols()
    if not symbols:
        logger.error("No symbols found in symbols.txt")
        return False
    
    logger.info(f"Starting agent with {len(symbols)} symbols")
    
    # Create Cerebro instance with special settings for live trading
    cerebro = bt.Cerebro(cheat_on_open=True)
    cerebro.addstrategy(Agent)
    
    # Set up broker
    broker = AlpacaPaperTradingBroker(
        api_key=api_key,
        secret_key=secret_key,
        account_id=account_id
    )
    cerebro.setbroker(broker)
    
    # Add data feeds
    for symbol in symbols:
        # Determine topic name based on symbol format (crypto vs stock)
        topic_name = 'crypto-data' if '/' in symbol else 'market-data'
        
        # Create data feed
        data = PubSubMarketDataFeed(
            project_id=project_id,
            topic_name=topic_name,
            symbol=symbol
        )
        cerebro.adddata(data, name=symbol)
        logger.info(f"Added data feed for {symbol}")
    
    # Record starting portfolio value
    starting_value = cerebro.broker.getvalue()
    logger.info(f"Initial portfolio value: ${starting_value:.2f}")
    
    # First initialize the strategy
    logger.info("Initializing strategy")
    cerebro.run(runonce=False, preload=False, writer=False)
    
    # Then start all data feeds
    logger.info("Starting data feeds")
    for data in cerebro.datas:
        try:
            data.start()
        except Exception as e:
            logger.error(f"Error starting data feed for {data._name}: {e}")
            # Continue with other data feeds
    
    # Write initial heartbeat
    write_heartbeat()
    
    # Main trading loop
    logger.info(f"Entering live trading loop (polling every {poll_interval}s)")
    last_heartbeat = time.time()
    last_report = time.time()
    
    try:
        while running:
            # Process any new data
            wait_for_first_bar(cerebro)
            cerebro.run()
            
            # Update heartbeat every 5 minutes
            now = time.time()
            if now - last_heartbeat >= 300:
                write_heartbeat()
                last_heartbeat = now
            
            # Log portfolio value every hour
            if now - last_report >= 3600:
                current_value = cerebro.broker.getvalue()
                pnl = current_value - starting_value
                logger.info(f"Portfolio value: ${current_value:.2f} (P&L: ${pnl:.2f})")
                last_report = now
            
            # Process order status
            cerebro.broker.notify()
            
            # Poll interval
            time.sleep(poll_interval)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in main loop: {e}", exc_info=True)
    finally:
        # Clean up resources
        logger.info("Shutting down agent...")
        for data in cerebro.datas:
            try:
                if hasattr(data, 'stop'):
                    data.stop()
            except Exception as e:
                logger.error(f"Error stopping data feed for {data._name}: {e}")
        
        logger.info("Agent shutdown complete")
    
    return True

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the agent
    success = run_agent()
    sys.exit(0 if success else 1)