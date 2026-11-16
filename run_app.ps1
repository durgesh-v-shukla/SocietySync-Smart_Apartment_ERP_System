# SocietySync ERP - Run Application Script (PowerShell)

# Load DATABASE_URL from .env file if it exists
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*DATABASE_URL\s*=\s*(.+)\s*$') {
            $env:DATABASE_URL = $Matches[1]
        }
    }
}

# If DATABASE_URL is still not set, prompt the user
if (-not $env:DATABASE_URL) {
    Write-Host "No .env file found or DATABASE_URL not set." -ForegroundColor Red
    Write-Host "  Example: postgresql://postgres:yourpassword@localhost:5432/societysync" -ForegroundColor Gray
    $env:DATABASE_URL = Read-Host "Enter DATABASE_URL"
}

# Mask the password for display
$maskedUrl = $env:DATABASE_URL -replace '(://[^:]+:)[^@]+(@)', '${1}***${2}'

# Display startup information
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  SocietySync ERP - Starting Application" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Database: $maskedUrl" -ForegroundColor Yellow
Write-Host "Port:     8501" -ForegroundColor Yellow
Write-Host ""
Write-Host "Access the application at:" -ForegroundColor Green
Write-Host "  -> http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Run Streamlit application
streamlit run app.py --server.port 8501
