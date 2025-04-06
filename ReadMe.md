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