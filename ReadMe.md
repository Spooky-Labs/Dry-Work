# Usage Instructions

## 1. Set up GKE cluster and namespace:
```bash
kubectl create namespace trading-agents
```

## 2. Create Alpaca credentials secret:
```bash
kubectl create secret generic alpaca-credentials \
  --namespace=trading-agents \
  --from-literal=api-key=YOUR_BROKER_API_KEY \
  --from-literal=secret-key=YOUR_BROKER_SECRET_KEY \
  --from-literal=account-id=YOUR_ACCOUNT_ID
```

## 3. Deploy your Firebase function:
```bash
firebase deploy --only functions:deployTradingAgent
```
## 4. Add the deploy button to your web interface:
```html
<button onclick="deployAgent('AGENT_ID')">Deploy to Paper Trading</button>

<script>
function deployAgent(agentId) {
  const deployFunction = firebase.functions().httpsCallable('deployTradingAgent');
  deployFunction({ agentId: agentId })
    .then((result) => {
      console.log('Deployment successful:', result.data);
      alert('Agent deployed successfully!');
    })
    .catch((error) => {
      console.error('Deployment failed:', error);
      alert('Deployment failed: ' + error.message);
    });
}
</script>
```

This minimal implementation provides the foundational structure for your trading agent platform while keeping complexity manageable.




2025-04-10 05:56:36,207 - trading_agent - INFO - Starting agent with 2 symbols
2025-04-10 05:56:36,207 - broker - INFO - Alpaca Broker client initialized
2025-04-10 05:56:36,476 - broker - INFO - Account refreshed - Cash: $1234.56, Equity: $1234.56
2025-04-10 05:56:36,584 - broker - INFO - Positions refreshed - 0 active positions
2025-04-10 05:56:36,585 - data_feed - INFO - Initialized PubSub data feed for AAPL
2025-04-10 05:56:36,585 - trading_agent - INFO - Added data feed for AAPL
2025-04-10 05:56:36,586 - data_feed - INFO - Initialized PubSub data feed for X
2025-04-10 05:56:36,586 - trading_agent - INFO - Added data feed for X
2025-04-10 05:56:36,586 - trading_agent - INFO - Initial portfolio value: $1234.56
2025-04-10 05:56:36,586 - trading_agent - INFO - Initializing strategy
2025-04-10 05:56:39,450 - data_feed - INFO - Created subscription: projects/the-farm-neutrino/subscriptions/feed-AAPL-11f0ddc40
2025-04-10 05:56:39,451 - data_feed - INFO - Starting subscription for AAPL
2025-04-10 05:56:39,453 - data_feed - INFO - Data feed started for AAPL
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1744289799.457219 12971084 fork_posix.cc:75] Other threads are currently calling into gRPC, skipping fork() handlers
2025-04-10 05:56:42,315 - data_feed - INFO - Created subscription: projects/the-farm-neutrino/subscriptions/feed-X-11fcc6f30
2025-04-10 05:56:42,316 - data_feed - INFO - Starting subscription for X
2025-04-10 05:56:42,318 - data_feed - INFO - Data feed started for X
2025-04-10 05:56:42,329 - data_feed - INFO - Stopping data feed for AAPL
2025-04-10 05:56:43,440 - data_feed - INFO - Deleted subscription: projects/the-farm-neutrino/subscriptions/feed-AAPL-11f0ddc40
2025-04-10 05:56:43,440 - data_feed - INFO - Data feed stopped for AAPL
2025-04-10 05:56:43,441 - data_feed - INFO - Stopping data feed for X
2025-04-10 05:56:44,468 - data_feed - INFO - Deleted subscription: projects/the-farm-neutrino/subscriptions/feed-X-11fcc6f30
2025-04-10 05:56:44,469 - data_feed - INFO - Data feed stopped for X
2025-04-10 05:56:44,469 - trading_agent - INFO - Starting data feeds
2025-04-10 05:56:47,127 - data_feed - INFO - Created subscription: projects/the-farm-neutrino/subscriptions/feed-AAPL-11f0ddc40
2025-04-10 05:56:47,128 - data_feed - INFO - Starting subscription for AAPL
2025-04-10 05:56:47,130 - data_feed - INFO - Data feed started for AAPL
I0000 00:00:1744289807.151701 12971084 fork_posix.cc:75] Other threads are currently calling into gRPC, skipping fork() handlers
2025-04-10 05:56:49,864 - data_feed - INFO - Created subscription: projects/the-farm-neutrino/subscriptions/feed-X-11fcc6f30
2025-04-10 05:56:49,865 - data_feed - INFO - Starting subscription for X
2025-04-10 05:56:49,866 - data_feed - INFO - Data feed started for X
2025-04-10 05:56:49,868 - trading_agent - WARNING - Failed to write heartbeat: [Errno 13] Permission denied: '/var/lib/trading-agent'
2025-04-10 05:56:49,868 - trading_agent - INFO - Entering live trading loop (polling every 60.0s)
2025-04-10 05:56:49,868 - trading_agent - ERROR - Error in main loop: 'Cerebro' object has no attribute 'runonce'
Traceback (most recent call last):
  File "/Users/nonplus/Documents/Spooky Labs/Dry Work/runner.py", line 138, in run_agent
    cerebro.runonce()
    ^^^^^^^^^^^^^^^
AttributeError: 'Cerebro' object has no attribute 'runonce'. Did you mean: '_runonce'?
2025-04-10 05:56:49,872 - trading_agent - INFO - Shutting down agent...
2025-04-10 05:56:49,873 - data_feed - INFO - Stopping data feed for AAPL
2025-04-10 05:56:50,915 - data_feed - INFO - Deleted subscription: projects/the-farm-neutrino/subscriptions/feed-AAPL-11f0ddc40
2025-04-10 05:56:50,915 - data_feed - INFO - Data feed stopped for AAPL
2025-04-10 05:56:50,915 - data_feed - INFO - Stopping data feed for X
2025-04-10 05:56:51,991 - data_feed - INFO - Deleted subscription: projects/the-farm-neutrino/subscriptions/feed-X-11fcc6f30
2025-04-10 05:56:51,991 - data_feed - INFO - Data feed stopped for X
2025-04-10 05:56:51,991 - trading_agent - INFO - Agent shutdown complete