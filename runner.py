# Remove these credentials after development
api_key = "CKI6JH8CDEZIIO3T7BK5" # Broker Keys
secret_key = "X4TCzbWAcmkabqps7XRpc7vIk7oasVlmFwbdmCGo" # Broker secret key
account_id = "105830c9-e690-4549-8d66-3048a3c5c6a2" # Account ID for Eloquent Swanson ACCT #: 789220144
project_id = "the-farm-neutrino"
poll_interval = 60
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


def signal_handler(sig, frame):
    """Handle termination signals for graceful shutdown"""
    global running
    logger.info("Shutdown signal received")
    running = False

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
    
    # Get symbols to trade
    symbols = get_symbols()
    if not symbols:
        logger.error("No symbols found in symbols.txt")
        return False
    
    logger.info(f"Starting agent with {len(symbols)} symbols")
    
    # Create Cerebro instance with special settings for live trading
    cerebro = bt.Cerebro(stdstats=False)
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
            symbol=symbol,
        )
        cerebro.adddata(data, name=symbol)
        logger.info(f"Added data feed for {symbol}")
    
    # Record starting portfolio value
    starting_value = cerebro.broker.getvalue()
    logger.info(f"Initial portfolio value: ${starting_value:.2f}")
    
    # First initialize the strategy
    logger.info("Initializing strategy")

    try:
        # Run the live trading engine - Backtrader handles the loop
        logger.info("Starting live trading engine...")
        cerebro.run(live=True) # REMOVED the preload/runonce/exactbars here for simplicity, live=True implies much of this.

        # --- The code will block here until Cerebro finishes (e.g., by signal) ---

        logger.info("Trading engine finished.")
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error during Cerebro run: {e}", exc_info=True)
    finally:
        # (Optional but good) Clean up resources if needed,
        # though Cerebro/data feeds might handle their own shutdown.
        # Data feed stop calls might be handled by Cerebro's exit.
        logger.info("Agent shutdown process starting...")
        # Explicitly stopping feeds might still be useful depending on implementation
        # for data in cerebro.datas:
        #     if hasattr(data, 'stop'): data.stop()
        # Clean up resources
        for data in cerebro.datas:
            try:
                if hasattr(data, 'stop'):
                    data.stop()
            except Exception as e:
                logger.error(f"Error stopping data feed for {data._name}: {e}")
        
        logger.info("Agent shutdown complete")
    
    # Record final value
    final_value = cerebro.broker.getvalue()
    logger.info(f"Final portfolio value: ${final_value:.2f}")

    return True

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the agent
    success = run_agent()
    sys.exit(0 if success else 1)