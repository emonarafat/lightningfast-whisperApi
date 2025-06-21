# Whisper API CLI Launcher Menu — PowerShell Edition

function Test-Command {
    param([string]$name)
    if (Get-Command $name -ErrorAction SilentlyContinue) {
        Write-Host "✅ Found: $name" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ Missing: $name" -ForegroundColor Red
        return $false
    }
}

# 🔍 Check required CLI tools
$requiredTools = @("az", "docker", "git")
$missing = 0
Write-Host "`n🔎 Checking required tools..." -ForegroundColor Cyan
foreach ($tool in $requiredTools) {
    if (-not (Test-Command $tool)) { $missing++ }
}
if ($missing -gt 0) {
    Write-Host "`n🚫 One or more required tools are missing. Exiting." -ForegroundColor Red
    exit 1
}

# 📜 Define menu
$menuItems = @(
    @{ Label = "🔨 Build Docker image"; Action = { docker build -t whisperacr.azurecr.io/whisper-api:latest . } }
    @{ Label = "📤 Push image to Azure Container Registry"; Action = { docker push whisperacr.azurecr.io/whisper-api:latest } }
    @{ Label = "🚀 Deploy to Azure Container Instance (interactive)"; Action = { .\azure_deploy.ps1 } }
    @{ Label = "⚡ Deploy to ACI (silent from .env.deploy)"; Action = { .\azure_deploy.ps1 -NoPrompt } }
    @{ Label = "🧪 View .env.deploy variables"; Action = {
        if (Test-Path ".env.deploy") {
            Write-Host "`n📄 .env.deploy contents:`n" -ForegroundColor Cyan
            Get-Content .env.deploy | ForEach-Object {
                if ($_ -notmatch "^\s*#") {
                    Write-Host ("  " + $_) -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "`n⚠️  .env.deploy not found." -ForegroundColor DarkYellow
        }
    }}
    @{ Label = "❌ Exit"; Action = { Write-Host "`n👋 Goodbye!" -ForegroundColor Cyan; exit } }
)

function Show-Menu {
    Clear-Host
    Write-Host "======= ⚙ Azure Whisper API Launcher =======" -ForegroundColor Cyan
    for ($i = 0; $i -lt $menuItems.Count; $i++) {
        Write-Host "[$($i + 1)] $($menuItems[$i].Label)"
    }
    return Read-Host "`nSelect an option (1-$($menuItems.Count))"
}

# 🌀 Menu loop
while ($true) {
    $selection = Show-Menu
    if ($selection -match '^\d+$' -and [int]$selection -in 1..$menuItems.Count) {
        Clear-Host
        & $menuItems[$selection - 1].Action
        Write-Host "`n⏎ Press Enter to return to the menu..." -ForegroundColor DarkGray
        [void][System.Console]::ReadLine()
    } else {
        Write-Host "`n❗ Invalid selection. Please enter a number between 1 and $($menuItems.Count)." -ForegroundColor Red
        Start-Sleep -Seconds 1
    }
}
