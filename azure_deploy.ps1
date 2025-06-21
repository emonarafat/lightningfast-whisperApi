param(
    [switch]$NoPrompt = $false
)

# ───── Pre-flight: check required tools ─────
function Test-Command($name) {
    $exists = Get-Command $name -ErrorAction SilentlyContinue
    if ($exists) {
        Write-Host "✅ Found: $name" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ Missing: $name" -ForegroundColor Red
        return $false
    }
}

Write-Host "`n🔍 Checking required tools..." -ForegroundColor Cyan
$tools = @("az", "docker", "git")
$missing = 0
foreach ($tool in $tools) {
    if (-not (Test-Command $tool)) { $missing++ }
}
if ($missing -gt 0) {
    Write-Host "`n🚫 Missing required tools. Install them before proceeding." -ForegroundColor Red
    exit 1
}

# ───── Load and display .env.deploy ─────
$envFile = ".env.deploy"
if (Test-Path $envFile) {
    Write-Host "`n📄 Loading settings from $envFile..." -ForegroundColor Cyan
    try {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^\s*#') { return }
            if ($_ -match '^\s*(\w+)\s*=\s*(.+)\s*$') {
                $name  = $matches[1].Trim()
                $value = $matches[2].Trim().Trim("'`"`"")
                Set-Item -Path "env:$name" -Value $value
                Write-Host ("  {0,-20}: " -f $name) -NoNewline -ForegroundColor Gray
                Write-Host $value -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "❌ Failed to load environment variables." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  No $envFile file found." -ForegroundColor DarkYellow
}

function PromptOrDefault($label, $default) {
    if ($NoPrompt) { return $default }
    $input = Read-Host "$label [$default]"
    return if (![string]::IsNullOrWhiteSpace($input)) { $input } else { $default }
}

# ───── Collect config values ─────
$ACR_NAME        = PromptOrDefault "🔐 ACR Name"         ($env:ACR_NAME        ?? "whisperacr")
$RESOURCE_GROUP  = PromptOrDefault "🔧 Resource Group"   ($env:RESOURCE_GROUP  ?? "whisper-rg")
$ACI_NAME        = PromptOrDefault "📦 ACI Name"         ($env:ACI_NAME        ?? "whisper-api")
$LOCATION        = PromptOrDefault "🌍 Azure Location"   ($env:LOCATION        ?? "eastus")
$DNS_LABEL       = PromptOrDefault "🌐 DNS Label"        ($env:DNS_LABEL       ?? "whisper-api-demo")
$DOCKER_IMAGE    = PromptOrDefault "🐳 Docker Image Tag" ($env:DOCKER_IMAGE    ?? "whisper-api:latest")
$WHISPER_MODEL   = PromptOrDefault "🧠 WHISPER_MODEL"    ($env:WHISPER_MODEL   ?? "openai/whisper-medium")
$WHISPER_DEVICE  = PromptOrDefault "⚙️ WHISPER_DEVICE"   ($env:WHISPER_DEVICE  ?? "cpu")
$CHUNK_SEC       = PromptOrDefault "📏 CHUNK_SEC"        ($env:CHUNK_SEC       ?? "60")
$WORKER_COUNT    = PromptOrDefault "🔁 WORKER_COUNT"     ($env:WORKER_COUNT    ?? "4")
$IMAGE_TAG       = "$ACR_NAME.azurecr.io/$DOCKER_IMAGE"

# ───── Summary ─────
Write-Host "`n🧾 Configuration Summary" -ForegroundColor Cyan
@{
    "ACR"            = $ACR_NAME
    "Resource Group" = $RESOURCE_GROUP
    "ACI Name"       = $ACI_NAME
    "Location"       = $LOCATION
    "DNS Label"      = $DNS_LABEL
    "Image Tag"      = $IMAGE_TAG
    "Model"          = $WHISPER_MODEL
    "Device"         = $WHISPER_DEVICE
    "Chunk Seconds"  = $CHUNK_SEC
    "Worker Count"   = $WORKER_COUNT
}.GetEnumerator() | ForEach-Object {
    Write-Host ("  {0,-15}: " -f $_.Key) -NoNewline -ForegroundColor Gray
    Write-Host $_.Value -ForegroundColor Yellow
}

# ───── Azure setup ─────
az account show > $null 2>&1; if ($LASTEXITCODE -ne 0) { az login | Out-Null }
if (-not (az group exists --name $RESOURCE_GROUP | ConvertFrom-Json)) {
    az group create --name $RESOURCE_GROUP --location $LOCATION | Out-Null
}
if (-not (az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP -o none 2>$null)) {
    az acr create --name $ACR_NAME --resource-group $RESOURCE_GROUP --sku Basic --location $LOCATION | Out-Null
}
az acr login --name $ACR_NAME | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Login to ACR failed. Exiting." -ForegroundColor Red
    exit 1
}

# ───── Docker build ─────
Write-Host "🐋 Building Docker image..." -ForegroundColor Cyan
docker build -t "$IMAGE_TAG" .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed. Exiting." -ForegroundColor Red
    exit 1
}

# ───── Optional push ─────
$push = $true
if (-not $NoPrompt) {
    $resp = Read-Host "📤 Push image to ACR? [Y/n]"
    if ($resp -ne "" -and $resp -notmatch "^[Yy]$") { $push = $false }
}
if ($push) {
    docker push "$IMAGE_TAG"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Push failed. Exiting." -ForegroundColor Red
        exit 1
    }
}

# ───── Optional deploy ─────
$deploy = $true
if (-not $NoPrompt) {
    $resp = Read-Host "🚀 Deploy to ACI? [Y/n]"
    if ($resp -ne "" -and $resp -notmatch "^[Yy]$") { $deploy = $false }
}
if ($deploy) {
    $ACR_USERNAME = az acr credential show --name $ACR_NAME --query "username" -o tsv
    $ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv

    Write-Host "🚀 Creating Azure Container Instance..." -ForegroundColor Cyan
    az container create `
      --name "$ACI_NAME" `
      --resource-group "$RESOURCE_GROUP" `
      --image "$IMAGE_TAG" `
      --registry-login-server "$ACR_NAME.azurecr.io" `
      --registry-username "$ACR_USERNAME" `
      --registry-password "$ACR_PASSWORD" `
      --cpu 2 `
      --memory 4 `
      --dns-name-label "$DNS_LABEL" `
      --ports 80 `
      --environment-variables `
          WHISPER_MODEL="$WHISPER_MODEL" `
          WHISPER_DEVICE="$WHISPER_DEVICE" `
          CHUNK_SEC="$CHUNK_SEC" `
          WORKER_COUNT="$WORKER_COUNT" `
          PYTHONDONTWRITEBYTECODE=1 `
          PYTHONUNBUFFERED=1 `
          TRANSFORMERS_CACHE="/app/.cache/huggingface" `
      --restart-policy OnFailure `
      --no-wait

    Write-Host "`n🌐 Deployed at:" -ForegroundColor Green
    Write-Host "   http://$DNS_LABEL.$LOCATION.azurecontainer.io/docs`n"
} else {
    Write-Host "🛑 Deployment skipped." -ForegroundColor DarkYellow
}
