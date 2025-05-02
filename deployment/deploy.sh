#!/bin/bash
# Deployment script for RAG system

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'  # No Color

# Environment - should be one of: dev, staging, prod
ENV=${1:-dev}
KUBE_NAMESPACE="rag-system"

# Add suffix to namespace for dev/staging
if [ "$ENV" = "dev" ]; then
    KUBE_NAMESPACE="rag-system-dev"
elif [ "$ENV" = "staging" ]; then
    KUBE_NAMESPACE="rag-system-staging"
fi

# Configuration paths
CONFIG_DIR="./kubernetes"
SECRETS_FILE="./secrets/${ENV}.yaml"

# Check kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}kubectl is not installed. Please install kubectl and try again.${NC}"
    exit 1
fi

# Check for secrets file
if [ ! -f "$SECRETS_FILE" ]; then
    echo -e "${RED}Secrets file not found: $SECRETS_FILE${NC}"
    echo -e "${YELLOW}Create a secrets file or run with a valid environment: dev, staging, or prod${NC}"
    exit 1
fi

# Print deployment info
echo -e "${GREEN}Deploying RAG System to ${YELLOW}$ENV${GREEN} environment...${NC}"
echo -e "Namespace: ${YELLOW}$KUBE_NAMESPACE${NC}"

# Create namespace if it doesn't exist
kubectl get namespace $KUBE_NAMESPACE > /dev/null 2>&1 || kubectl create namespace $KUBE_NAMESPACE

# Apply secrets
echo -e "${GREEN}Applying secrets...${NC}"
kubectl apply -f "$SECRETS_FILE" --namespace="$KUBE_NAMESPACE"

# Apply database resources
echo -e "${GREEN}Deploying database...${NC}"
kubectl apply -f "$CONFIG_DIR/database-deployment.yaml" --namespace="$KUBE_NAMESPACE"

# Wait for database to be ready
echo -e "${GREEN}Waiting for database to be ready...${NC}"
kubectl rollout status statefulset/rag-db --namespace="$KUBE_NAMESPACE" --timeout=300s

# Apply Redis resources
echo -e "${GREEN}Deploying Redis...${NC}"
kubectl apply -f "$CONFIG_DIR/redis-deployment.yaml" --namespace="$KUBE_NAMESPACE"

# Wait for Redis to be ready
echo -e "${GREEN}Waiting for Redis to be ready...${NC}"
kubectl rollout status deployment/rag-redis --namespace="$KUBE_NAMESPACE" --timeout=120s

# Apply API resources
echo -e "${GREEN}Deploying API...${NC}"

# Replace environment variables in deployment file
sed "s/\${DOCKER_REGISTRY}/$DOCKER_REGISTRY/g; s/\${TAG}/$TAG/g" \
    "$CONFIG_DIR/rag-deployment.yaml" | kubectl apply -f - --namespace="$KUBE_NAMESPACE"

# Wait for API to be ready
echo -e "${GREEN}Waiting for API to be ready...${NC}"
kubectl rollout status deployment/rag-api --namespace="$KUBE_NAMESPACE" --timeout=300s

# Apply HPA
echo -e "${GREEN}Applying Horizontal Pod Autoscaler...${NC}"
kubectl apply -f "$CONFIG_DIR/horizontal-pod-autoscaler.yaml" --namespace="$KUBE_NAMESPACE"

# Get service URL
echo -e "${GREEN}Deployment complete!${NC}"
if [ "$ENV" = "prod" ]; then
    INGRESS_HOST=$(kubectl get ingress rag-api-ingress -n "$KUBE_NAMESPACE" -o jsonpath='{.spec.rules[0].host}')
    echo -e "API is available at: ${YELLOW}https://$INGRESS_HOST${NC}"
else
    SERVICE_IP=$(kubectl get svc rag-api -n "$KUBE_NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -z "$SERVICE_IP" ]; then
        SERVICE_IP=$(kubectl get svc rag-api -n "$KUBE_NAMESPACE" -o jsonpath='{.spec.clusterIP}')
        echo -e "API is available inside the cluster at: ${YELLOW}http://$SERVICE_IP${NC}"
    else
        echo -e "API is available at: ${YELLOW}http://$SERVICE_IP${NC}"
    fi
fi

echo -e "${GREEN}Deployment to $ENV environment completed successfully!${NC}"