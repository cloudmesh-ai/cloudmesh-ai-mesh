!/bin/bash

# Local AI Cluster Deployment Script
# This script automates the deployment of the cluster using the CloudMesh-AI orchestrator.

echo "🚀 Starting Local AI Cluster Deployment..."

# Check if python3 is installed
if ! command -v python3 &> /dev/null
then
    echo "❌ Error: python3 could not be found. Please install it to proceed."
    exit 1
fi

# Run the orchestrator
python3 deploy_cluster.py

if [ $? -eq 0 ]; then
    echo ""
    echo "----------------------------------------------------------------"
    echo "💻 LAPTOP (Control Plane)"
    echo "----------------------------------------------------------------"
    echo "1. Ensure you can reach http://localhost:4000 (via SSH tunnel to WHITE)"
    echo "2. Run the agent:"
    echo "   python3 src/agent.py"
    echo "----------------------------------------------------------------"
    echo "✅ Deployment process complete."
else
    echo "❌ Deployment failed. Please check the logs above."
    exit 1
fi