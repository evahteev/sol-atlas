#!/bin/bash
#set -eux
# Ensure required environment variables are set
: "${CLUSTER_NAME:?CLUSTER_NAME is not set}"
: "${K8S_API:?K8S_API is not set}"
: "${CI_TOKEN:?CI_TOKEN is not set}"
: "${KUBE_NAMESPACE:?KUBE_NAMESPACE is not set}"
: "${STACK_NAME:?STACK_NAME is not set}"
: "${HELM_CHART:?HELM_CHART is not set}"
: "${IMAGE_TAG:?IMAGE_TAG is not set}"
: "${IMAGE_APP:?IMAGE_APP is not set}"
: "${SERVICE:?SERVICE is not set}"
: "${APP:?APP is not set}"
: "${STAGE:?STAGE is not set}"

# Print all environment variables
# echo "CLUSTER_NAME: ${CLUSTER_NAME}"
# echo "K8S_API: ${K8S_API}"
# echo "CI_TOKEN: ${CI_TOKEN}"
# echo "KUBE_NAMESPACE: ${KUBE_NAMESPACE}"
# echo "STACK_NAME: ${STACK_NAME}"
# echo "HELM_CHART: ${HELM_CHART}"
# echo "IMAGE_TAG: ${IMAGE_TAG}"
# echo "IMAGE_APP: ${IMAGE_APP}"

# Configure kubectl
kubectl config set-cluster ${CLUSTER_NAME} --server=${K8S_API} --insecure-skip-tls-verify=true
kubectl config set-credentials ${CLUSTER_NAME} --token=${CI_TOKEN}
kubectl config set-context ${CLUSTER_NAME} --cluster=${CLUSTER_NAME} --user=${CLUSTER_NAME}
kubectl config use-context ${CLUSTER_NAME}

for NAMESPACE in ${KUBE_NAMESPACE}; do
    echo "...."
    echo "Service ${STACK_NAME}-${SERVICE}-${APP} deploy to ${NAMESPACE} namespace"
    echo " "

    # Deploy using Helm
    helm upgrade --install ${STACK_NAME}-${SERVICE}-${APP} ${HELM_CHART} \
      --wait \
      --namespace ${NAMESPACE} \
      --create-namespace \
      --set appName=frontend \
      --set ${STACK_NAME}.sidecarImageTag=${IMAGE_TAG} \
      --set image=${IMAGE_APP} \
      --set imageTag=${IMAGE_TAG} \
      --set kubeNamespace=${NAMESPACE} \
      -f helm/envs/${SERVICE}-${STAGE}/values.yaml \
      -f helm/envs/${SERVICE}-${STAGE}/${SERVICE}-${APP}.yaml \
      --history-max=2

    echo " "
    helm history ${STACK_NAME}-${SERVICE}-${APP} -n ${NAMESPACE}
    echo " "
    echo "...."
done

if [ "$fail" == "true" ]; then
    exit 1
fi
