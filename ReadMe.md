# Dry Work

This repository contains the code for a Python-based trading agent using the Backtrader framework. It integrates with Google Cloud Pub/Sub for real-time market data and Alpaca's Broker API for paper trading execution. The agent can be run locally or deployed to Google Kubernetes Engine (GKE) via Firebase Cloud Functions.

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

* **Market Data:** Market data is published to Google Cloud Pub/Sub topics (`market-data` or `crypto-data`)[cite: 3].
* **Data Ingestion:** The `PubSubMarketDataFeed` subscribes to the relevant Pub/Sub topic based on the symbol and feeds data into Backtrader.
* **Trading Logic:** The `Agent` strategy within Backtrader analyzes the data (e.g., using SMA crossovers) and makes trading decisions.
* **Order Execution:** The `AlpacaPaperTradingBroker` interacts with the Alpaca Broker API to place and manage paper trading orders for a specified account.
* **Deployment (Optional):** A Firebase Cloud Function (`app.js`) can trigger a Cloud Build process to containerize the agent and deploy it to a GKE cluster using the provided Kubernetes manifest (`PaperTrading.yaml`).

## Components

| Component         | Purpose                                                                 | File                |
| :---------------- | :---------------------------------------------------------------------- | :------------------ |
| Runner            | Main script to initialize and run the Backtrader engine                 | `runner.py` [cite: 3]         |
| Pub/Sub Data Feed | Custom Backtrader feed to consume data from Google Cloud Pub/Sub        | `data_feed.py`      |
| Alpaca Broker     | Custom Backtrader broker to interact with Alpaca's Broker API           | `broker.py`       |
| Trading Agent     | The core trading strategy logic (example: SMA crossover)                | `agent/agent.py`    |
| Symbols List      | Text file containing the symbols the agent should trade                 | `symbols.txt` [cite: 1]     |
| Requirements      | Lists necessary Python libraries                                        | `requirements.txt`  |
| K8s Manifest      | Kubernetes deployment configuration for running the agent on GKE        | `PaperTrading.yaml`|
| Deployment Func   | Firebase Cloud Function to automate the build and GKE deployment process | `app.js`         |

## Prerequisites

* Python 3.x
* `pip` for installing Python packages
* Google Cloud Platform account with billing enabled
* `gcloud` CLI installed and configured
* Alpaca account (Paper Trading) with API Key, Secret Key, and Account ID
* **(Optional - for GKE Deployment)** `kubectl` installed
* **(Optional - for GKE Deployment)** Firebase project and `firebase` CLI installed
* **(Optional - for GKE Deployment)** Appropriate IAM permissions to create GKE deployments, Cloud Builds, and manage Pub/Sub.

## Repository Structure

```
├── agent/
│   └── agent.py          # Trading strategy logic
├── app.js                # Firebase function for deployment (optional)
├── broker.py             # Alpaca broker implementation
├── data_feed.py          # Pub/Sub data feed implementation
├── PaperTrading.yaml     # Kubernetes deployment manifest (optional)
├── ReadMe.md             # This file (or the original minimal one)
├── requirements.txt      # Python dependencies
├── runner.py             # Main application runner
└── symbols.txt           # List of trading symbols
```

## Local Execution Instructions

1.  **Clone the repository.**
2.  **Configure Credentials:**
    * **Important:** The current `runner.py` has hardcoded credentials[cite: 3]. **Do not commit these directly.** It is strongly recommended to use environment variables or a secure secret management system.
    * Set the following environment variables (or modify `runner.py` temporarily, **but be careful**):
        ```bash
        export ALPACA_API_KEY="YOUR_ALPACA_API_KEY"
        export ALPACA_SECRET_KEY="YOUR_ALPACA_SECRET_KEY"
        export ALPACA_ACCOUNT_ID="YOUR_ALPACA_ACCOUNT_ID"
        export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
        ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Symbols:** Edit `symbols.txt` [cite: 1] and add the market symbols you want the agent to trade (e.g., `AAPL`, `BTC/USD`). Ensure the Pub/Sub topics (`market-data`, `crypto-data`) exist in your GCP project and are receiving data for these symbols[cite: 3].
5.  **Run the Agent:**
    ```bash
    python runner.py
    ```

## GKE Deployment Instructions (Optional)

These steps assume you want to use the Firebase/GKE deployment method outlined in `app.js` and `PaperTrading.yaml`.

1.  **Set up GKE Cluster:** Ensure you have a GKE cluster running and `kubectl` is configured to connect to it.
2.  **Create Namespace:**
    ```bash
    kubectl create namespace trading-agents
    ```
3.  **Create Alpaca Secret:** Store your Alpaca credentials securely in the cluster.
    ```bash
    kubectl create secret generic alpaca-credentials \
      --namespace=trading-agents \
      --from-literal=api-key=YOUR_ALPACA_API_KEY \
      --from-literal=secret-key=YOUR_ALPACA_SECRET_KEY \
      --from-literal=account-id=YOUR_ALPACA_ACCOUNT_ID
    ```
4.  **Set up Firebase:**
    * Initialize Firebase in your project directory (`firebase init`).
    * Deploy the `deployTradingAgent` function defined in `app.js`:
        ```bash
        firebase deploy --only functions
        ```
5.  **Prepare Source Code:** Zip your agent source code (excluding secrets) and upload it to a GCS bucket accessible by Cloud Build (e.g., `gs://agent-source-code/<userId>/<agentId>/agent-source.zip` as referenced in `app.js`). The `agentId` should match an entry in your Firestore database if using the full flow from `app.js`.
6.  **Trigger Deployment:** Call the deployed Firebase function (e.g., via a web UI as shown in the original `ReadMe.md` or directly) providing the `agentId`. The function will use Cloud Build to create the Docker image and `kubectl` to apply the `PaperTrading.yaml` manifest to your GKE cluster.

## Security Considerations

* **Secret Management:** Avoid hardcoding API keys and secrets. Use environment variables for local execution or Kubernetes secrets for GKE deployments[cite: 3].
* **Permissions:** Ensure the service accounts used (for Pub/Sub access, Alpaca API interaction, GKE deployment) follow the principle of least privilege.

## Troubleshooting

| Issue                                        | Resolution                                                                                                                               |
| :------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------- |
| `runner.py` fails with API key errors        | Ensure `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_ACCOUNT_ID`, `GOOGLE_CLOUD_PROJECT` environment variables are set correctly.         |
| No data received by the agent              | Verify Pub/Sub topics exist, are receiving data with the correct format and `symbol` attribute, and the agent has permission to subscribe. |
| Order placement fails (`broker.py`)          | Check Alpaca account status, API key permissions, and ensure the `account_id` is correct for the Broker API.                     |
| GKE deployment fails                         | Check Cloud Build logs for errors. Verify GKE cluster connectivity, namespace existence, and secret creation.              |
| Backtrader errors during `cerebro.run()`   | Examine the logs (`runner.py` configures logging [cite: 3]). Check data format, strategy logic (`agent.py`), and broker interaction (`broker.py`). |