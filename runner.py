# Remove these credentials after development
# api_key = "CKI6JH8CDEZIIO3T7BK5" # Broker Keys
# secret_key = "X4TCzbWAcmkabqps7XRpc7vIk7oasVlmFwbdmCGo" # Broker secret key
# account_id = "105830c9-e690-4549-8d66-3048a3c5c6a2" # Account ID for Eloquent Swanson ACCT #: 789220144

#!/usr/bin/env python3
import backtrader as bt
import logging
import time
import signal
import sys
import os
from datetime import datetime

# Import our custom components
from data_feed import DynamicPubSubFeed
from broker import AlpacaPaperTradingBroker
from agent.agent import Agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('trader')

# Global control flag
running = True

def signal_handler(sig, frame):
    """Handle termination signals"""
    global running
    logger.info("Shutdown signal received")
    running = False

def write_heartbeat():
    """Write a heartbeat file for health checks"""
    try:
        # Ensure directory exists
        os.makedirs('/var/lib/trading-agent', exist_ok=True)
        
        # Write timestamp
        heartbeat_file = '/var/lib/trading-agent/heartbeat'
        with open(heartbeat_file, 'w') as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        logger.warning(f"Failed to write heartbeat: {e}")
        
def run_trading():
    """Run the trading agent"""
    # Get configuration from environment
    api_key = os.environ.get('ALPACA_API_KEY')
    secret_key = os.environ.get('ALPACA_SECRET_KEY')
    account_id = os.environ.get('ALPACA_ACCOUNT_ID')
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    
    # Get polling interval from environment or use default
    try:
        polling_interval = float(os.environ.get('POLLING_INTERVAL', '3600.0'))
        # Ensure reasonable bounds (1 minute to 1 day)
        polling_interval = max(60, min(86400, polling_interval))
    except ValueError:
        logger.warning("Invalid polling interval, using default of 60.0 second")
        polling_interval = 60.0
    
    # Validate configuration
    if not all([api_key, secret_key, account_id, project_id]):
        logger.error("Missing required environment variables")
        return False
    
    # Load symbols
    try:
        with open("symbols.txt", "r") as f:
            symbols = [line.strip() for line in f if line.strip()]
        
        if not symbols:
            logger.error("No symbols defined in symbols.txt")
            return False
    except Exception as e:
        logger.error(f"Error reading symbols: {e}")
        return False
    
    # Initialize Backtrader
    cerebro = bt.Cerebro()
    
    # Set up broker
    cerebro.setbroker(AlpacaPaperTradingBroker(
        api_key=api_key,
        secret_key=secret_key,
        account_id=account_id
    ))
    
    # Add data feeds for each symbol
    for symbol in symbols:
        # Select appropriate topic
        topic_name = 'crypto-data' if '/' in symbol else 'market-data'
        
        # Create data feed
        data = DynamicPubSubFeed(
            project_id=project_id,
            topic_name=topic_name,
            symbol=symbol
        )
        cerebro.adddata(data, name=symbol)
    
    # Add agent strategy
    cerebro.addstrategy(Agent)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', 
                       riskfreerate=0.01, timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.Calmar, _name='calmar')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annualreturn')
    
    # Initialize
    logger.info(f"Starting agent with {len(symbols)} symbols")
    cerebro.run()
    
    # Record starting portfolio value
    starting_value = cerebro.broker.getvalue()
    logger.info(f"Initial portfolio value: ${starting_value:.2f}")
    
    # Write initial heartbeat
    write_heartbeat()
    
    # Main trading loop
    logger.info(f"Entering live trading loop (polling every {polling_interval}s)")
    last_heartbeat = time.time()
    
    while running:
        try:
            # Process new data
            cerebro.runonce()
            
            # Update heartbeat every 5 minutes
            now = time.time()
            if now - last_heartbeat >= 300:
                write_heartbeat()
                last_heartbeat = now
                
                # Log current performance
                current_value = cerebro.broker.getvalue()
                logger.info(f"Portfolio value: ${current_value:.2f}")
            
            # Wait for next polling interval
            time.sleep(polling_interval)
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            time.sleep(polling_interval * 5)  # Longer delay on error
    
    # Clean up data feeds
    for data in cerebro.datas:
        if hasattr(data, 'stop'):
            data.stop()
    
    logger.info("Trading agent stopped")
    return True

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the agent
    success = run_trading()
    sys.exit(0 if success else 1)