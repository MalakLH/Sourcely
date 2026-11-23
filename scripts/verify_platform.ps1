# Sourcely Platform Verification Script
# Run this after docker-compose up --build -d

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Sourcely Platform Verification" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check service health
Write-Host "1. Checking Service Health..." -ForegroundColor Yellow
Write-Host ""

$services = @(
    @{Name="Agent Service"; URL="http://localhost:8000/health"},
    @{Name="Docs Service"; URL="http://localhost:8002/health"},
    @{Name="Webguide Service"; URL="http://localhost:8003/health"},
    @{Name="Scanner Service"; URL="http://localhost:8004/health"},
    @{Name="UI Service"; URL="http://localhost:8501/_stcore/health"}
)

foreach ($service in $services) {
    try {
        $response = Invoke-RestMethod -Uri $service.URL -TimeoutSec 5 -ErrorAction Stop
        Write-Host "  ✓ $($service.Name): HEALTHY" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ $($service.Name): UNREACHABLE" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "2. Testing Agent API Routing..." -ForegroundColor Yellow
Write-Host ""

# Test docs route
try {
    $query = @{query = "What is a Kubernetes Pod?"} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/query" `
        -Method Post `
        -Body $query `
        -ContentType "application/json" `
        -TimeoutSec 30
    
    Write-Host "  ✓ Docs Route: tool=$($response.tool_used), time=$($response.execution_time_ms)ms" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ Docs Route: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

# Test web route
try {
    $query = @{query = "Find FastAPI tutorials"} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/query" `
        -Method Post `
        -Body $query `
        -ContentType "application/json" `
        -TimeoutSec 30
    
    Write-Host "  ✓ Web Route: tool=$($response.tool_used), time=$($response.execution_time_ms)ms" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ Web Route: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "3. Testing Scanner Service..." -ForegroundColor Yellow
Write-Host ""

try {
    $scanPayload = @{
        code = "query = 'SELECT * FROM users WHERE id = ' + user_id"
        language = "python"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:8004/scan" `
        -Method Post `
        -Body $scanPayload `
        -ContentType "application/json" `
        -TimeoutSec 30
    
    Write-Host "  ✓ Scanner: $($response.total_findings) findings, scanners=$($response.scanners_used -join ', ')" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ Scanner: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "4. Checking LanceDB Stats..." -ForegroundColor Yellow
Write-Host ""

try {
    $stats = Invoke-RestMethod -Uri "http://localhost:8002/stats" -TimeoutSec 5
    $vectorStore = $stats.vector_store
    
    if ($vectorStore.exists) {
        Write-Host "  ✓ LanceDB: $($vectorStore.count) chunks in $($vectorStore.table_name)" -ForegroundColor Green
    }
    else {
        Write-Host "  ! LanceDB: Empty (run POST /ingest/all to populate)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ✗ LanceDB: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Verification Complete!" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Ingest full corpus: curl -X POST http://localhost:8002/ingest/all" -ForegroundColor White
Write-Host "  2. Open UI: http://localhost:8501" -ForegroundColor White
Write-Host "  3. Test all features in browser" -ForegroundColor White
Write-Host ""
