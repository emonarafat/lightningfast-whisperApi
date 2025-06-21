#!/bin/bash

# ──────────────── Load .env.deploy if exists ──────────────── #
ENV_FILE=".env.deploy"
if [[ -f "$ENV_FILE" ]]; then
  echo "📄 Loading settings from $ENV_FILE..."
  set -o allexport
  source "$ENV_FILE"
  set +o allexport
fi

# ──────────────── Default Values ──────────────── #
DEFAULT_ACR_NAME="${ACR_NAME:-whisperacr}"
DEFAULT_RESOURCE_GROUP="${RESOURCE_GROUP:-whisper-rg}"
DEFAULT_ACI_NAME="${ACI_NAME:-whisper-api}"
DEFAULT_LOCATION="${LOCATION:-eastus}"
DEFAULT_DNS_LABEL="${DNS_LABEL:-whisper-api-demo}"
DEFAULT_IMAGE_NAME="${DOCKER_IMAGE:-whisper-api:latest}"
DEFAULT_WHISPER_MODEL="${WHISPER_MODEL:-openai/whisper-medium}"
DEFAULT_WHISPER_DEVICE="${WHISPER_DEVICE:-cpu}"
DEFAULT_CHUNK_SEC="${CHUNK_SEC:-60}"
DEFAULT_WORKER_COUNT="${WORKER_COUNT:-4}"

# ──────────────── Mode Detection ──────────────── #
PROMPT_MODE=true
[[ "$1" == "--no-prompt" ]] && PROMPT_MODE=false

# ──────────────── Interactive Prompts ──────────────── #
prompt_or_default() {
  local var_name=$1
  local default_value=$2
  if $PROMPT_MODE; then
    read -p "$var_name [$default_value]: " input
    echo "${input:-$default_value}"
  else
    echo "$default_value"
  fi
}

ACR_NAME=$(prompt_or_default "🔐 ACR Name" "$DEFAULT_ACR_NAME")
RESOURCE_GROUP=$(prompt_or_default "🔧 Azure Resource Group" "$DEFAULT_RESOURCE_GROUP")
ACI_NAME=$(prompt_or_default "📦 ACI Name" "$DEFAULT_ACI_NAME")
LOCATION=$(prompt_or_default "🌍 Azure Location" "$DEFAULT_LOCATION")
DNS_LABEL=$(prompt_or_default "🌐 DNS Label" "$DEFAULT_DNS_LABEL")
IMAGE_NAME=$(prompt_or_default "🐳 Docker Image Tag" "$DEFAULT_IMAGE_NAME")
WHISPER_MODEL=$(prompt_or_default "🧠 WHISPER_MODEL" "$DEFAULT_WHISPER_MODEL")
WHISPER_DEVICE=$(prompt_or_default "⚙️ WHISPER_DEVICE" "$DEFAULT_WHISPER_DEVICE")
CHUNK_SEC=$(prompt_or_default "📏 CHUNK_SEC" "$DEFAULT_CHUNK_SEC")
WORKER_COUNT=$(prompt_or_default "🔁 WORKER_COUNT" "$DEFAULT_WORKER_COUNT")

IMAGE_TAG="${ACR_NAME}.azurecr.io/${IMAGE_NAME}"

# ──────────────── Summary ──────────────── #
echo
echo "──────────────────────────────────────────────"
echo " Azure Whisper API — Final Configuration"
echo "──────────────────────────────────────────────"
echo "ACR           : $ACR_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo "ACI Name      : $ACI_NAME"
echo "Location      : $LOCATION"
echo "DNS Label     : $DNS_LABEL"
echo "Image Tag     : $IMAGE_TAG"
echo "Model         : $WHISPER_MODEL"
echo "Device        : $WHISPER_DEVICE"
echo "Chunk Seconds : $CHUNK_SEC"
echo "Worker Count  : $WORKER_COUNT"
echo "──────────────────────────────────────────────"
echo

# ──────────────── Azure + ACR ──────────────── #
az account show &>/dev/null || az login
az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null || \
az acr create --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --sku Basic --location "$LOCATION"
az acr login --name "$ACR_NAME"

# ──────────────── Docker Build + Push ──────────────── #
docker build -t "$IMAGE_TAG" .

if $PROMPT_MODE; then
  read -p "📤 Push image to ACR? [Y/n]: " push
  push="${push:-Y}"
else
  push="Y"
fi

if [[ "$push" =~ ^[Yy]$ ]]; then
  docker push "$IMAGE_TAG"
fi

# ──────────────── Deploy ──────────────── #
if $PROMPT_MODE; then
  read -p "🚀 Deploy to Azure Container Instance? [Y/n]: " deploy
  deploy="${deploy:-Y}"
else
  deploy="Y"
fi

if [[ "$deploy" =~ ^[Yy]$ ]]; then
  ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query "username" -o tsv)
  ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

  az container create \
    --name "$ACI_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$IMAGE_TAG" \
    --registry-login-server "${ACR_NAME}.azurecr.io" \
    --registry-username "$ACR_USERNAME" \
    --registry-password "$ACR_PASSWORD" \
    --cpu 2 \
    --memory 4 \
    --dns-name-label "$DNS_LABEL" \
    --ports 80 \
    --environment-variables \
      WHISPER_MODEL="$WHISPER_MODEL" \
      WHISPER_DEVICE="$WHISPER_DEVICE" \
      CHUNK_SEC="$CHUNK_SEC" \
      WORKER_COUNT="$WORKER_COUNT" \
      PYTHONDONTWRITEBYTECODE=1 \
      PYTHONUNBUFFERED=1 \
      TRANSFORMERS_CACHE=/app/.cache/huggingface \
    --restart-policy OnFailure \
    --no-wait

  echo
  echo "🌐 Deployed at: http://${DNS_LABEL}.${LOCATION}.azurecontainer.io/docs"
else
  echo "🛑 Deployment skipped."
fi
