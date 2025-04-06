// index.js
const functions = require('firebase-functions');
const admin = require('firebase-admin');
const {Storage} = require('@google-cloud/storage');
const {CloudBuildClient} = require('@google-cloud/cloudbuild');
const {ContainerAnalysisClient} = require('@google-cloud/containeranalysis');
const {GKEClient} = require('@google-cloud/container');

admin.initializeApp();
const storage = new Storage();
const db = admin.firestore();
const cloudbuild = new CloudBuildClient();
const gkeClient = new GKEClient();

exports.deployTradingAgent = functions.https.onCall(async (data, context) => {
  // Verify authentication
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'User must be logged in');
  }
  
  const userId = context.auth.uid;
  const agentId = data.agentId;
  
  try {
    // 1. Get agent information from Firestore
    const agentRef = db.collection('agents').doc(agentId);
    const agentDoc = await agentRef.get();
    
    if (!agentDoc.exists || agentDoc.data().userId !== userId) {
      throw new functions.https.HttpsError('permission-denied', 'Agent not found or not owned by user');
    }
    
    // 2. Update agent status
    await agentRef.update({
      status: 'deploying',
      deploymentStarted: admin.firestore.FieldValue.serverTimestamp()
    });
    
    // 3. Build Docker image
    const projectId = process.env.GCP_PROJECT;
    const buildResult = await cloudbuild.createBuild({
      projectId,
      build: {
        source: {
          storageSource: {
            bucket: 'agent-source-code',
            object: `${userId}/${agentId}/agent-source.zip`
          }
        },
        steps: [
          {
            name: 'gcr.io/cloud-builders/docker',
            args: [
              'build',
              '-t', `gcr.io/${projectId}/trading-agent-${agentId}`,
              '.'
            ]
          }
        ],
        images: [
          `gcr.io/${projectId}/trading-agent-${agentId}`
        ]
      }
    });
    
    // 4. Wait for build to complete
    const [build] = await buildResult[0].promise();
    
    if (build.status !== 'SUCCESS') {
      throw new Error(`Build failed: ${build.status}`);
    }
    
    // 5. Deploy to GKE
    const cluster = await gkeClient.getCluster({
      name: 'projects/my-project/locations/us-central1/clusters/trading-cluster'
    });
    
    // Create deployment manifest
    const deploymentManifest = `
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: trading-agent-${agentId}
        namespace: trading-agents
      spec:
        replicas: 1
        selector:
          matchLabels:
            app: trading-agent
            agent-id: ${agentId}
        template:
          metadata:
            labels:
              app: trading-agent
              agent-id: ${agentId}
          spec:
            containers:
            - name: agent
              image: gcr.io/${projectId}/trading-agent-${agentId}
              env:
              - name: ALPACA_API_KEY
                valueFrom:
                  secretKeyRef:
                    name: alpaca-credentials
                    key: api-key
              - name: ALPACA_SECRET_KEY
                valueFrom:
                  secretKeyRef:
                    name: alpaca-credentials
                    key: secret-key
              - name: ALPACA_ACCOUNT_ID
                valueFrom:
                  secretKeyRef:
                    name: alpaca-credentials
                    key: account-id
              resources:
                requests:
                  memory: "256Mi"
                  cpu: "100m"
                limits:
                  memory: "512Mi"
                  cpu: "200m"
    `;
    
    // Apply the manifest using gcloud container kubectl
    const kubectl = await cloudbuild.createBuild({
      projectId,
      build: {
        steps: [
          {
            name: 'gcr.io/cloud-builders/kubectl',
            args: [
              'apply',
              '-f',
              '-'
            ],
            env: [
              `CLOUDSDK_COMPUTE_ZONE=us-central1`,
              `CLOUDSDK_CONTAINER_CLUSTER=trading-cluster`
            ],
            script: deploymentManifest
          }
        ]
      }
    });
    
    // 6. Update agent status
    await agentRef.update({
      status: 'deployed',
      deploymentCompleted: admin.firestore.FieldValue.serverTimestamp(),
      kubernetesDeployment: `trading-agent-${agentId}`
    });
    
    return {
      success: true,
      agentId: agentId,
      deploymentName: `trading-agent-${agentId}`
    };
    
  } catch (error) {
    console.error('Deployment error:', error);
    
    // Update agent status on failure
    await db.collection('agents').doc(agentId).update({
      status: 'deployment_failed',
      error: error.message
    });
    
    throw new functions.https.HttpsError('internal', `Deployment failed: ${error.message}`);
  }
});