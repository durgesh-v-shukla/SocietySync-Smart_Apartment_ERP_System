# SocietySync ERP - Run Application Script (PowerShell)

# Set the database connection URL
$env:DATABASE_URL = "postgresql://postgres:root@localhost:5432/societysync"

# Display startup information
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  🏢 SocietySync ERP - Starting Application" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Database: postgresql://postgres:***@localhost:5432/societysync" -ForegroundColor Yellow
Write-Host "Port:     8501" -ForegroundColor Yellow
Write-Host ""
Write-Host "Access the application at:" -ForegroundColor Green
Write-Host "  → http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Run Streamlit application
streamlit run app.py --server.port 8501