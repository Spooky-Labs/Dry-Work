#!/usr/bin/env python3
import backtrader as bt
import os
import time
from alpaca.data.timeframe import TimeFrame

# Import custom components
from broker import AlpacaMinimalBroker
from data_feed import AlpacaMinimalData
from agent.agent import Agent

def run_trading():
    """Simple paper trading implementation using Alpaca"""
    # Get API credentials from environment
    # api_key = os.environ.get('ALPACA_API_KEY')
    # secret_key = os.environ.get('ALPACA_SECRET_KEY')
    # account_id = os.environ.get('ALPACA_ACCOUNT_ID')

    # Remove these credentials after development
    api_key = "CKI6JH8CDEZIIO3T7BK5" # Broker Keys
    secret_key = "X4TCzbWAcmkabqps7XRpc7vIk7oasVlmFwbdmCGo" # Broker secret key
    account_id = "105830c9-e690-4549-8d66-3048a3c5c6a2" # Account ID for Eloquent Swanson ACCT #: 789220144

    # Define trading symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

    # Initialize Cerebro
    cerebro = bt.Cerebro()

    # Set up Alpaca broker
    broker = AlpacaMinimalBroker(
        api_key=api_key,
        secret_key=secret_key,
        account_id=account_id
    )
    cerebro.setbroker(broker)

    # Add strategy
    cerebro.addstrategy(Agent, fast_period=10, slow_period=30)

    # Add data feeds for each symbol
    for symbol in symbols:
        data = AlpacaMinimalData(
            api_key=api_key,
            secret_key=secret_key,
            symbol=symbol,
            timeframe=TimeFrame.Day
        )
        cerebro.adddata(data, name=symbol)
        print(f"Added data feed for {symbol}")

    # Initialize and run once
    strategies = cerebro.run(stdstats=False)
    print(f"Initial portfolio value: ${cerebro.broker.getvalue():.2f}")

    # Simple trading loop
    try:
        while True:
            # Refresh account data
            broker.refresh_account()
            
            # Process new data for each feed
            for data in cerebro.datas:
                data._load()  # Fetch latest data
            
            # Execute strategy logic
            cerebro.runstrategies()
            
            # Log current value
            print(f"Current portfolio value: ${cerebro.broker.getvalue():.2f}")
            
            # Wait before next cycle
            time.sleep(300)  # 5 minutes between updates
            
    except KeyboardInterrupt:
        print("Trading stopped by user")
    except Exception as e:
        print(f"Error: {e}")

    print(f"Final portfolio value: ${cerebro.broker.getvalue():.2f}")

if __name__ == "__main__":
    run_trading()