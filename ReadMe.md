# Dry Work

# Alpaca Paper Trading Platform

A high-performance trading platform that connects the Backtrader framework with Alpaca's Broker API for paper trading, using Google Cloud Pub/Sub for real-time market data and GKE for deployment.

## Architecture

```mermaid
graph LR
    A[Market Data Source] --> B(Google Cloud Pub/Sub);
    B -- Market Data Stream --> C{PubSubMarketDataFeed (data_feed.py)};
    C --> D[Backtrader Cerebro (runner.py)];
    D --> E(Agent Strategy (agent/agent.py));
    E -- Trading Decisions --> F{AlpacaPaperTradingBroker (broker.py)};
    F -- Place/Manage Orders --> G[Alpaca Broker API];

    subgraph Deployment
        H[Firebase Web UI] -- Trigger Deploy --> I(Firebase Function (app.js));
        I -- Build & Deploy --> J(Google Cloud Build);
        J -- Deploy --> K(GKE Cluster);
        K -- Runs --> L[Trading Agent Pod (PaperTrading.yaml)];
    end

    style B fill:#f9f,stroke:#333,stroke-width:2px
    style G fill:#ccf,stroke:#333,stroke-width:2px
    style K fill:#f96,stroke:#333,stroke-width:2px
```

## Components

| Component         | Purpose                                                       | File                |
| :---------------- | :------------------------------------------------------------ | :------------------ |
| Runner            | Main script to initialize and run the Backtrader engine       | `runner.py`         |
| Pub/Sub Data Feed | Custom Backtrader feed to consume data from Google Cloud Pub/Sub | `data_feed.py`      |
| Alpaca Broker     | Custom Backtrader broker to interact with Alpaca's Broker API | `broker.py`         |
| Trading Agent     | The core trading strategy logic (example: SMA crossover)      | `agent/agent.py`    |
| Symbols List      | Text file containing the symbols the agent should trade       | `symbols.txt`       |
| Requirements      | Lists necessary Python libraries                              | `requirements.txt`  |
| K8s Manifest      | Kubernetes deployment configuration for running the agent     | `PaperTrading.yaml` |
| Deployment Func   | Firebase Cloud Function to automate the deployment process    | `app.js`            |

## Data Flow

1. **Market Data Ingestion**: Market data is published to Google Cloud Pub/Sub topics (`market-data` or `crypto-data`).
2. **Data Processing**: The `PubSubMarketDataFeed` subscribes to the Pub/Sub topic based on the symbol and feeds data into Backtrader.
3. **Trading Logic**: The `Agent` strategy analyzes the data (using SMA crossovers) and makes trading decisions.
4. **Order Execution**: The `AlpacaPaperTradingBroker` interacts with the Alpaca Broker API to place and manage paper trading orders.
5. **Deployment Flow**: A Firebase Cloud Function can trigger a Cloud Build process to containerize and deploy the agent to GKE.

## Prerequisites

- Python 3.9+
- Google Cloud Platform account with billing enabled
- `gcloud` CLI installed and configured
- Alpaca account (Paper Trading) with API Key, Secret Key, and Account ID
- For deployment: `kubectl` installed and Firebase project configured

## Repository Structure

```
├── agent/
│   └── agent.py          # Trading strategy logic
├── app.js                # Firebase function for deployment
├── broker.py             # Alpaca broker implementation
├── data_feed.py          # Pub/Sub data feed implementation
├── PaperTrading.yaml     # Kubernetes deployment manifest
├── ReadMe.md             # This file
├── requirements.txt      # Python dependencies
├── runner.py             # Main application runner
└── symbols.txt           # List of trading symbols
```

## Local Execution Instructions

1. **Clone the repository**

2. **Configure Credentials:**
   ```bash
   export ALPACA_API_KEY="YOUR_ALPACA_API_KEY"
   export ALPACA_SECRET_KEY="YOUR_ALPACA_SECRET_KEY"
   export ALPACA_ACCOUNT_ID="YOUR_ALPACA_ACCOUNT_ID"
   export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Symbols:**
   Edit `symbols.txt` with the market symbols you want to trade (e.g., `AAPL`, `BTC/USD`).
   Ensure the Pub/Sub topics exist in your GCP project and are receiving data.

5. **Run the Agent:**
   ```bash
   python runner.py
   ```

## GKE Deployment Instructions

1. **Set up GKE Cluster:**
   Ensure you have a GKE cluster running and `kubectl` is configured to connect to it.

2. **Create Namespace:**
   ```bash
   kubectl create namespace trading-agents
   ```

3. **Create Alpaca Secret:**
   ```bash
   kubectl create secret generic alpaca-credentials \
     --namespace=trading-agents \
     --from-literal=api-key=YOUR_ALPACA_API_KEY \
     --from-literal=secret-key=YOUR_ALPACA_SECRET_KEY \
     --from-literal=account-id=YOUR_ALPACA_ACCOUNT_ID
   ```

4. **Set up Firebase:**
   * Initialize Firebase in your project directory:
     ```bash
     firebase init
     ```
   * Deploy the function:
     ```bash
     firebase deploy --only functions
     ```

5. **Prepare Source Code:**
   Zip your agent code and upload to a GCS bucket accessible by Cloud Build:
   ```bash
   zip -r agent-source.zip . -x "*.git*"
   gsutil cp agent-source.zip gs://agent-source-code/<userId>/<agentId>/
   ```

6. **Trigger Deployment:**
   Call the deployed Firebase function to start the deployment process.
   
## Security Considerations

- **Secret Management:** Use environment variables for local execution and Kubernetes secrets for GKE.
- **Permissions:** Follow the principle of least privilege for service accounts.
- **Network Security:** Restrict Pod communication to necessary services only.
- **Container Security:** Use non-root users in containers as implemented in the Dockerfile.

## Monitoring and Logging

- Agent logs are automatically configured using Python's logging module.
- For deployed agents, use `kubectl logs` to view container logs:
  ```bash
  kubectl logs -n trading-agents -l app=trading-agent
  ```
- Use GCP Cloud Monitoring for long-term metrics and alerting.

## Troubleshooting

| Issue                                      | Resolution                                                   |
| :----------------------------------------- | :----------------------------------------------------------- |
| API key authentication errors              | Verify API keys and ensure environment variables are set correctly |
| No data received by the agent              | Check Pub/Sub topics exist and agent has subscription permissions |
| Order placement fails                      | Verify Alpaca account status and API key permissions          |
| GKE deployment fails                       | Check Cloud Build logs and GKE cluster connectivity           |
| Backtrader errors during execution         | Examine agent logs for data format or strategy logic issues   |

## Development and Extension

To modify the trading strategy:
1. Edit `agent/agent.py` with your custom logic
2. Test locally with paper trading
3. Deploy to GKE for continuous operation

For production environments:
- Implement more robust error handling
- Add monitoring and alerting
- Consider implementing position tracking persistence