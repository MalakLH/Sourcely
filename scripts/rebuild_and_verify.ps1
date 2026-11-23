# Sourcely - Rebuild and Verify Script
# Rebuilds all containers and runs verification tests

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Sourcely Platform - Rebuild & Verify" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop and rebuild containers
Write-Host "Step 1: Rebuilding containers..." -ForegroundColor Yellow
Set-Location "C:\Users\user\Documents\Coding Projects\Sourcely\infrastructure\docker"

Write-Host "  Stopping containers..." -ForegroundColor Gray
docker-compose down

Write-Host "  Building and starting containers (this may take 3-5 minutes)..." -ForegroundColor Gray
docker-compose up --build -d

Write-Host "  Waiting 15 seconds for services to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 15

Write-Host "✓ Containers rebuilt" -ForegroundColor Green
Write-Host ""

# Step 2: Check service health
Write-Host "Step 2: Checking service health..." -ForegroundColor Yellow

$services = @(
    @{Name="Agent"; URL="http://localhost:8000/health"},
    @{Name="Docs"; URL="http://localhost:8002/health"},
    @{Name="Webguide"; URL="http://localhost:8003/"},
    @{Name="Scanner"; URL="http://localhost:8004/health"},
    @{Name="Sandbox"; URL="http://localhost:8001/health"},
    @{Name="UI"; URL="http://localhost:8501/_stcore/health"}
)

foreach ($svc in $services) {
    try {
        $response = Invoke-RestMethod -Uri $svc.URL -TimeoutSec 5 -ErrorAction Stop
        Write-Host "  ✓ $($svc.Name): HEALTHY" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ $($svc.Name): ERROR" -ForegroundColor Red
    }
}

Write-Host ""

# Step 3: Wait for docs auto-ingestion
Write-Host "Step 3: Waiting for docs auto-ingestion (15 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

try {
    $stats = Invoke-RestMethod -Uri "http://localhost:8002/stats" -TimeoutSec 5
    $count = $stats.vector_store.count
    Write-Host "  ✓ LanceDB: $count chunks indexed" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ LanceDB stats unavailable" -ForegroundColor Red
}

Write-Host ""

# Step 4: Run tests
Write-Host "Step 4: Running verification tests..." -ForegroundColor Yellow
Write-Host ""

# Test 1: Docs Expert
Write-Host "Test 1: Docs Expert (Kubernetes Liveness Probes)" -ForegroundColor Cyan
try {
    $body = @{query = "How do Kubernetes Liveness Probes work?"} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/query" `
        -Method Post `
        -Body $body `
        -ContentType "application/json" `
        -TimeoutSec 90
    
    Write-Host "  ✓ Tool: $($response.tool_used)" -ForegroundColor Green
    Write-Host "  ✓ Confidence: $($response.confidence)" -ForegroundColor Green
    Write-Host "  ✓ Citations: $($response.citations.Count)" -ForegroundColor Green
    Write-Host "  ✓ Answer length: $($response.answer.Length) chars" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 2: GitHub Search
Write-Host "Test 2: GitHub Search (No 500 Errors)" -ForegroundColor Cyan
try {
    $body = @{query = "search GitHub repo that use langchain"} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/query" `
        -Method Post `
        -Body $body `
        -ContentType "application/json" `
        -TimeoutSec 90
    
    Write-Host "  ✓ Tool: $($response.tool_used)" -ForegroundColor Green
    Write-Host "  ✓ Status: $($response.status)" -ForegroundColor Green
    Write-Host "  ✓ Citations: $($response.citations.Count)" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 3: Sandbox Execution
Write-Host "Test 3: Sandbox Execution" -ForegroundColor Cyan
try {
    $body = @{
        query = "run this code"
        code = "print('Hello Sourcely')"
    } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/query" `
        -Method Post `
        -Body $body `
        -ContentType "application/json" `
        -TimeoutSec 90
    
    Write-Host "  ✓ Tool: $($response.tool_used)" -ForegroundColor Green
    Write-Host "  ✓ Answer preview: $($response.answer.Substring(0, [Math]::Min(100, $response.answer.Length)))" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Open UI: http://localhost:8501" -ForegroundColor White
Write-Host "  2. Verify light theme with no sidebar" -ForegroundColor White
Write-Host "  3. Test all features in browser" -ForegroundColor White
Write-Host "  4. Commit and push changes" -ForegroundColor White
Write-Host ""
