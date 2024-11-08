#!/bin/bash

# Variables
RELEASE_NAME="rabbitmq"
NAMESPACE="nft-mania"
RABBITMQ_HOSTNAME="nft-mania-rabbitmq.apps.dexguru.net" # Desired host for RabbitMQ management console
RABBITMQ_PASSWORD="wBD8wlShhitEFlPa" # Specify a strong password

# Create namespace if it doesn't exist
kubectl get namespace $NAMESPACE >/dev/null 2>&1 || kubectl create namespace $NAMESPACE

# Add the Bitnami repository if it's not added
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Deploy RabbitMQ with custom configurations
helm install $RELEASE_NAME bitnami/rabbitmq \
  --namespace $NAMESPACE \
  --set auth.username=rabbitmq \
  --set auth.password=$RABBITMQ_PASSWORD \
  --set auth.erlangCookie=secretcookie \
  --set ingress.enabled=true \
  --set ingress.hostname=$RABBITMQ_HOSTNAME \
  --set ingress.tls="true" \
  --set ingress.selfSigned="true" \
  --set ingress.annotations."kubernetes\.io/ingress\.class"="nginx" \
  --set ingress.annotations."nginx\.ingress\.kubernetes\.io/force-ssl-redirect"="\"true\"" \
  --set persistence.enabled=true \
  --set persistence.size=8Gi \
  --set resources.limits.cpu=500m \
  --set resources.limits.memory=512Mi \
  --set resources.requests.cpu=200m \
  --set resources.requests.memory=256Mi

# Wait for RabbitMQ to be fully deployed
echo "Waiting for RabbitMQ to be fully deployed..."
kubectl rollout status statefulset/${RELEASE_NAME} -n $NAMESPACE

# Display management console access details
echo -e "\nRabbitMQ Management Console URL: https://$RABBITMQ_HOSTNAME"
echo "Username: rabbitmq"
echo "Password: $RABBITMQ_PASSWORD"

echo -e "\nRabbitMQ has been successfully deployed in the cluster!"
