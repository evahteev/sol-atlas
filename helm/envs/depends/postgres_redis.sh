#!/bin/bash -e
# Wrapper script for prod infra component installation to K8S cluster
# Requirements: Helm>=3.2, kubectl>=1.19

### Make sure the kubectl context is correct
KUBECTL_CONTEXT=$(kubectl config current-context | cut -d/ -f2)
CLUSTER_NAME="dg-apps-prod"
if [ "$CLUSTER_NAME" != "$KUBECTL_CONTEXT" ]; then
  echo "Error: kubectl context $KUBECTL_CONTEXT does not match the env $CLUSTER_NAME"
  exit 1
fi

# Define namespace variable
NAMESPACE="nft-mania"

# Pull Bitnami charts
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install Bitnami PostgreSQL
helm upgrade --install postgres bitnami/postgresql \
  --namespace "$NAMESPACE" \
  --create-namespace \
  -f ./vars/postgres-values.yml

helm upgrade --install redis bitnami/redis \
  --namespace "$NAMESPACE" \
  --create-namespace \
  --set architecture=standalone \
  --set replica.replicaCount=0 \
  --set auth.enabled=false \
  --set persistence.enabled=false

echo "Deployment complete!"
